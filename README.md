# Stardew Valley RAG Conversational Agent

A multi-agent Retrieval-Augmented Generation (RAG) chatbot that answers Stardew Valley questions using grounded information from the public Stardew Valley Wiki, with support for multi-turn dialogues, intelligent parameter collection, and action execution.

## Project Overview

This project builds a conversational AI system for Stardew Valley that goes beyond simple question-answering. It combines:

- **Knowledge Retrieval**: Semantic search over 8,674 wiki chunks using FAISS vector store
- **Intent Classification**: LLM-based routing to 5 intent categories (CROPS, ITEMS, FRIENDSHIP, UNKNOWN, OFF_TOPIC)
- **Multi-Agent Architecture**: Specialized agents for farming, items, and relationships
- **Multi-Turn Dialogue**: Persistent session management across conversation turns
- **Action Execution**: Generate friendship plans, farm plans, and save favorite villagers with fuzzy name matching
- **Guardrails**: Off-topic detection and graceful error handling

Perfect for Stardew Valley players who want instant, wiki-grounded answers and strategic planning help.

## System Overview

The RAG system combines data preparation, semantic retrieval, intent routing, and action execution:

```
╔═══════════════════════════════════════════════════════════════════╗
║                    DATA PREPARATION PIPELINE                     ║
╚═══════════════════════════════════════════════════════════════════╝

Wiki Data (JSONL)
    ↓
chunker.py
    ├─ Load JSONL documents
    └─ Split into 512-char sections (64-char overlap)
    
    ↓
    
embeddings.py
    ├─ BAAI/bge-base-en-v1.5 embeddings
    └─ Embed all 8,674 chunks via A2 endpoint
    
    ↓
    
build_index.py
    ├─ Build FAISS vector index
    └─ Save index to disk (index/section_recursive/)

╔═══════════════════════════════════════════════════════════════════╗
║              RUNTIME MULTI-AGENT RAG PIPELINE                    ║
╚═══════════════════════════════════════════════════════════════════╝

Session Management (localStorage + Backend)
    ↓
User Query
    ↓
Orchestrator (orchestrator.py)
    ├─ LLM intent classification
    └─ Route to: CROPS | ITEMS | FRIENDSHIP | UNKNOWN | OFF_TOPIC
    
    ↓ ↓ ↓ ↓ ↓
    
    ┌─────────────────────────────────────────────────────────────┐
    │              KNOWLEDGE AGENTS (parallel)                    │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  CropPlanner      ItemFinder      FriendshipFinder      DefaultAgent
    │     Agent            Agent            Agent                Agent
    │       │                │                │                   │
    │       └────────────────┴────────────────┴───────────────────┘
    │                        │
    │             retriever.py (FAISS)
    │             • Embed query
    │             • Semantic search
    │             • Retrieve top-k wiki chunks
    │                        │
    │             llm.py (Qwen3-30B)
    │             • Augment with context
    │             • Generate grounded answer
    │                        │
    │        Output: Answer + Sources + Intent + Confidence
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
    
    OR (if action detected)
    
    ┌─────────────────────────────────────────────────────────────┐
    │         ACTION HANDLER (actions.py - separate flow)         │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Multi-turn Parameter Collection:                           │
    │  • CREATE_FRIENDSHIP_PLAN (villager, hearts, gifts/week)   │
    │  • CREATE_FARM_PLAN (plot_count, budget)                   │
    │  • SAVE_FAVORITES (auto-extract + fuzzy match)             │
    │                                                              │
    │  Validation → Parameter Refinement → Execution             │
    │  Output: Detailed action result with strategy & tips       │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘

Multi-Turn Conversation Flow:
    • Full history maintained per session
    • Action parameter collection across turns
    • Re-ask on validation failure with guidance
    • Execute and return result
```

**Key Capabilities:**
- ✅ Semantic knowledge retrieval with FAISS indexing
- ✅ Intent classification with 5 routing categories
- ✅ Multi-turn dialogue with session persistence
- ✅ Specialized knowledge agents (crops, items, friendship, general)
- ✅ Dedicated action handler for strategic planning
- ✅ Parameter validation with fuzzy name matching
- ✅ Off-topic detection and guardrails
- ✅ Graceful error handling with helpful guidance

## Key Technologies

| Component | Technology | Details |
|-----------|-----------|---------|
| **Embeddings** | BAAI/bge-base-en-v1.5 | Semantic similarity scoring |
| **Vector Store** | FAISS | 8,674 indexed wiki chunks |
| **LLM** | Qwen3-30B | OpenAI-compatible endpoint |
| **Framework** | FastAPI + LangChain | REST API + RAG pipeline |
| **Frontend** | HTML5 + Vanilla JS | Session management (localStorage) |
| **Session Mgmt** | In-memory + localStorage | 30-min timeout per session |

## Repository Structure

```text
Stardew_Valley_RAG/
├── README.md                       # Project overview (this file)
├── SETUP.md                        # Installation & running instructions
├── TESTING_GUIDE_UI.md             # 10-test verification suite
├── ARCHITECTURE.png                # Visual system diagram (WIP)
├── .env                            # Configuration (not committed)
├── requirements.txt                # Python dependencies
│
├── data/
│   ├── raw/                        # Raw scraped wiki sections
│   ├── interim/                    # Page-level aggregations
│   └── processed/
│       └── stardew_wiki_sections.jsonl   # 8,674 clean wiki chunks (RAG input)
│
├── src2/                           # Main RAG + Action implementation
│   ├── app.py                      # FastAPI server + web UI + multi-turn dialogue
│   ├── orchestrator.py             # LLM-based intent routing
│   ├── actions.py                  # 3 action handlers (friendship plan, farm plan, save favorites)
│   ├── retriever.py                # FAISS vector search
│   ├── llm.py                      # Qwen3 LLM client
│   ├── session_manager.py          # Session persistence
│   ├── chunker.py                  # Document chunking
│   ├── build_index.py              # Build FAISS index
│   ├── index.html                  # Stardew Valley themed UI (session-based)
│   ├── index/                      # FAISS index (generated, not committed)
│   └── tests/                      # 200+ unit & integration tests
│
├── docs/                           # Documentation
├── notebooks/                      # Exploration notebooks
└── tests/                          # Top-level tests
```

## Data

| File | Granularity | Records | Use |
|------|-------------|---------|-----|
| `raw/` | Section-level | 11,748 | Original scrape |
| `interim/` | Page-level | — | Intermediate aggregation |
| `processed/stardew_wiki_sections.jsonl` | Section-level | 8,674 (filtered) | ✅ RAG input |

Filters applied to processed data:
- Removed chunks under 50 characters
- Removed `Modding:` and `Module:` wiki pages
- Removed binary/corrupted records

## Chunking Strategy

Default: `section_recursive` — `RecursiveCharacterTextSplitter` with `chunk_size=512`, `chunk_overlap=64`.

Each chunk's `page_content` prepends the page title and heading before embedding:
```
'Watering Cans — Upgrades and Water Consumption\n<text>'
```
The original text is stored separately in metadata for clean citation display.

## LLM

Model: `qwen3-30b-a3b-fp8` with reasoning enabled via the course-provided endpoint.
Client uses the OpenAI-compatible API (`openai` Python package).

## Testing

See [TESTING_GUIDE_UI.md](TESTING_GUIDE_UI.md) for comprehensive 10-test verification suite.

### Requirement 2: Agent Capabilities ✅

| Capability | Status | Details |
|-----------|--------|---------|
| **Intent Classification** | ✅ | 5 intent types with LLM routing + confidence scoring |
| **Knowledge QA** | ✅ | RAG pipeline with source attribution (title, heading, URL, score) |
| **3+ Actions** | ✅ | Friendship plan, farm plan, save favorites (with fuzzy matching) |
| **Multi-Turn Dialogue** | ✅ | Parameter collection across turns with validation |
| **Conversation Memory** | ✅ | Full history per session (localStorage + backend) |
| **Guardrails** | ✅ | Off-topic detection, parameter validation, error handling |

### Requirement 3: Agent Evaluation ✅

**10 Comprehensive Tests:**
- **Phase 1** (Knowledge & Safety): Basic query, memory, off-topic, unknown intent
- **Phase 2** (Action Flows): Friendship plan (3 params), farm plan (2 params), save favorites (auto-complete)
- **Phase 3** (Error Handling): Invalid hearts, invalid budget, invalid/misspelled names

**Expected Pass Rate:** 100% (all edge cases handled gracefully)

## Setup & Installation

**For complete step-by-step installation and running instructions, see [SETUP.md](SETUP.md).**

This includes prerequisites, all 7 installation steps, running tests, troubleshooting, and API reference.

### **Demo**

[![Alt Text](https://github.com/user-attachments/assets/2c7e2a57-214b-44ca-ad87-e87d1da9d1e0)](https://www.youtube.com/watch?v=kNa_qY4sOPI)

