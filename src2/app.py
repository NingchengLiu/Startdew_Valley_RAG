"""
app.py — FastAPI RAG endpoint for the Stardew Valley conversational agent.

LLM  : qwen3-30b-a3b-fp8  (lab / local OpenAI-compatible endpoint)
Index: LangChain FAISS vectorstore  (built with build_index.py)

Endpoints
---------
    POST /chat      — Retrieve + generate (full RAG)
    POST /retrieve  — Retrieval only; useful for debugging chunk quality
    GET  /health    — Health check

Run
---
    export LLM_API_KEY=<your-student-id>
    export LLM_BASE_URL=https://rsm-8430-lab2.bjlkeng.io/v1
    uvicorn app:app --reload --port 8000

Environment variables
---------------------
    LLM_BASE_URL    — LLM endpoint base URL
    LLM_API_KEY     — API key / student ID
    LLM_MODEL       — model name (default: qwen3-30b-a3b-fp8)
    LLM_REASONING   — enable chain-of-thought (default: true)
    INDEX_DIR       — path to FAISS index directory (default: ./index/section_recursive)
    INDEX_STRATEGY  — which sub-directory to load (default: section_recursive)
"""

from __future__ import annotations

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from retriever import Retriever, RetrievedChunk
from llm import LLMClient, LLMResponse, get_llm_client
from orchestrator import route_intent, IntentType
from agents import get_agent, AgentResponse

# ── Config ─────────────────────────────────────────────────────────────────────

_strategy  = os.getenv("INDEX_STRATEGY", "section_recursive")
INDEX_DIR  = Path(os.getenv("INDEX_DIR",  f"index/{_strategy}"))

DEFAULT_TOP_K     = 3
MAX_HISTORY_TURNS = 6

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Stardew Valley RAG Agent",
    description="RAG agent grounded in the Stardew Valley Wiki — powered by qwen3-30b-a3b-fp8",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_retriever: Optional[Retriever]  = None
_llm:       Optional[LLMClient] = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever(INDEX_DIR)
    return _retriever


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = get_llm_client()
    return _llm


# ── Root endpoint (serve UI) ───────────────────────────────────────────────────

@app.get("/")
def serve_ui():
    """Serve the chat UI."""
    return FileResponse(Path(__file__).parent / "index.html")


# ── Schemas ────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role:    str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    query:                str          = Field(..., min_length=1, max_length=1000)
    conversation_history: list[Message] = Field(default_factory=list)
    top_k:                int          = Field(DEFAULT_TOP_K, ge=1, le=20)
    min_score:            float        = Field(0.25, ge=0.0, le=1.0)
    include_reasoning:    bool         = Field(False,
        description="Return the model's chain-of-thought in the response")


class SourceRef(BaseModel):
    page_title: str
    heading:    str
    url:        str
    score:      float


class ChatResponse(BaseModel):
    answer:              str
    sources:             list[SourceRef]
    retrieved_count:     int
    agent_type:          str          = Field(default="DefaultAgent",
        description="Which agent handled this query (ItemFinder, FriendshipFinder, CropPlanner, DefaultAgent, OffTopicFilter)")
    intent_type:         str          = Field(default="unknown",
        description="Intent classification (items, friendship, crops, unknown, off_topic)")
    intent_confidence:   float        = Field(default=0.0,
        description="Confidence score for intent classification (0.0 to 1.0)")
    intent_probabilities: dict        = Field(default_factory=dict,
        description="Probability distribution across all intent types")
    reasoning:           Optional[str] = Field(None,
        description="Qwen3 chain-of-thought (only when include_reasoning=true)")
    usage:               dict          = Field(default_factory=dict)


class RetrieveRequest(BaseModel):
    query:     str   = Field(..., min_length=1)
    top_k:     int   = Field(DEFAULT_TOP_K, ge=1, le=20)
    min_score: float = Field(0.0, ge=0.0, le=1.0)


class RetrieveResponse(BaseModel):
    query:  str
    chunks: list[dict]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    r   = get_retriever()
    llm = get_llm()
    return {
        "status":        "ok",
        "index_size":    r.index_size,
        "index_dir":     str(INDEX_DIR),
        "llm_model":     llm.model,
        "llm_reasoning": llm.reasoning,
    }


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    """Retrieval only — inspect what chunks are fetched for a query."""
    chunks = get_retriever().retrieve_with_threshold(
        req.query, top_k=req.top_k, min_score=req.min_score
    )
    return RetrieveResponse(
        query=req.query,
        chunks=[
            {
                "doc_id":     c.doc_id,
                "page_title": c.page_title,
                "heading":    c.heading,
                "text":       c.text,
                "url":        c.url,
                "score":      round(c.score, 4),
            }
            for c in chunks
        ],
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Multi-agent RAG pipeline:
      1. Route user query to appropriate agent (items, friendship, crops, or default)
      2. Check if question is off-topic (not about Stardew)
      3. Retrieve relevant wiki context
      4. Use specialized agent prompt to generate answer
      5. Return answer + sources + agent type + optional chain-of-thought
    """
    retriever = get_retriever()
    llm = get_llm()
    
    # Step 1: Route intent
    routed = route_intent(req.query)
    
    # Step 2: Check if off-topic
    if routed.intent_type == IntentType.OFF_TOPIC:
        return ChatResponse(
            answer="I'm designed to answer questions about Stardew Valley. Your question doesn't seem to be related to the game. Could you ask about farming, villagers, items, or other Stardew Valley topics?",
            sources=[],
            retrieved_count=0,
            agent_type="OffTopicFilter",
            intent_type="off_topic",
            intent_confidence=round(routed.confidence, 2),
            intent_probabilities=routed.probabilities or {},
            usage={},
        )
    
    # Step 3: Get appropriate agent
    agent_name = (
        routed.intent_type.value 
        if routed.intent_type != IntentType.UNKNOWN 
        else "default"
    )
    agent = get_agent(agent_name, retriever, llm)
    
    # Step 4: Get agent response
    agent_resp: AgentResponse = agent.answer(
        req.query,
        top_k=req.top_k,
        min_score=req.min_score,
        include_reasoning=req.include_reasoning,
    )
    
    # Step 5: Return
    return ChatResponse(
        answer=agent_resp.answer,
        sources=agent_resp.sources or [],
        retrieved_count=len(agent_resp.sources or []),
        agent_type=agent_resp.agent_type,
        intent_type=routed.intent_type.value,
        intent_confidence=round(routed.confidence, 2),
        intent_probabilities=routed.probabilities or {},
        reasoning=agent_resp.reasoning,
        usage=agent_resp.tokens_used or {},
    )
