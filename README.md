# Stardew Valley RAG Conversational Agent

A multi-agent Retrieval-Augmented Generation (RAG) chatbot that answers Stardew Valley questions using grounded information from the public Stardew Valley Wiki, with support for multi-turn dialogues, intelligent parameter collection, and action execution.

## Project Overview

This project builds a conversational AI system for Stardew Valley that goes beyond simple question-answering. It combines:

- **Knowledge Retrieval**: Semantic search over 13,813 indexed chunks using FAISS vector store
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
    └─ Embed all chunks via A2 endpoint
    
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
- ✅ Semantic knowledge retrieval with FAISS indexing (13,813 chunks)
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
| **Embeddings** | BAAI/bge-base-en-v1.5 | Semantic similarity via A2 endpoint |
| **Vector Store** | FAISS | 13,813 indexed chunks |
| **LLM** | Qwen3-30B | OpenAI-compatible endpoint |
| **Framework** | FastAPI + LangChain | REST API + RAG pipeline |
| **Frontend** | HTML5 + Vanilla JS | Session management (localStorage) |
| **Session Mgmt** | In-memory + localStorage | 30-min timeout per session |

## Repository Structure

```text
Stardew_Valley_RAG/
├── README.md                       # Project overview (this file)
├── SETUP.md                        # Installation & running instructions
├── TESTING_GUIDE_UI.md             # 10-test manual browser verification suite
├── DEPLOYMENT_GUIDE.md             # Deployment options (Render, Docker, Heroku)
├── .env                            # Configuration (not committed)
├── requirements.txt                # Python dependencies
│
├── data/
│   ├── raw/
│   │   └── stardew_wiki_extraction.jsonl   # 2,585 raw wiki page extractions
│   ├── interim/
│   │   └── stardew_wiki_cleaned.jsonl      # 2,585 cleaned page-level records
│   └── processed/
│       └── stardew_wiki_sections.jsonl     # 11,748 section-level wiki chunks
│
├── index/                          # FAISS vector index (generated by build_index.py)
│   └── section_recursive/
│       ├── index.faiss
│       ├── index.pkl
│       └── index_info.json
│
├── src/                            # Main RAG + Action implementation
│   ├── app.py                      # FastAPI server + web UI + multi-turn dialogue
│   ├── orchestrator.py             # LLM-based intent routing
│   ├── agents.py                   # Specialized knowledge agents (4 agents)
│   ├── actions.py                  # 3 action handlers (friendship plan, farm plan, save favorites)
│   ├── retriever.py                # FAISS vector search
│   ├── llm.py                      # Qwen3 LLM client with reasoning support
│   ├── session_manager.py          # Session persistence & conversation memory
│   ├── embeddings.py               # BAAI/bge-base-en-v1.5 embedding wrapper
│   ├── chunker.py                  # Document chunking strategies
│   ├── build_index.py              # Build FAISS index from JSONL
│   ├── index.html                  # Stardew Valley themed chat UI
│   ├── inspect_data.py             # Data inspection utility
│   └── test_llm.py                 # LLM connectivity test
│
├── evaluation/                     # Automated evaluation suite
│   ├── evaluation.py               # Test runner (16 test cases via /chat API)
│   ├── test_cases.json             # Test case definitions
│   ├── results.json                # Latest evaluation results
│   └── evaluation_result.md        # Evaluation report with analysis
│
└── tests/                          # Unit & integration tests
    ├── test_suite.py               # Comprehensive test suite (intent, actions, sessions)
    └── agent_tests/
        ├── test_integration.py     # Agent integration tests
        └── test_orchestrator.py    # Orchestrator routing tests
```

## Data

| File | Granularity | Records | Use |
|------|-------------|---------|-----|
| `raw/stardew_wiki_extraction.jsonl` | Page-level | 2,585 | Original wiki scrape |
| `interim/stardew_wiki_cleaned.jsonl` | Page-level | 2,585 | Cleaned aggregation |
| `processed/stardew_wiki_sections.jsonl` | Section-level | 11,748 | ✅ RAG input |

After chunking with `RecursiveCharacterTextSplitter(512, 64)`, the 11,748 sections produce **13,813 chunks** in the FAISS index.

Filters applied during processing:
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

See [TESTING_GUIDE_UI.md](TESTING_GUIDE_UI.md) for a more comprehensive 10-test verification suite.

In summary, the project uses a layered testing approach:

### Manual UI Testing
See [TESTING_GUIDE_UI.md](TESTING_GUIDE_UI.md) for 10 manual browser-based tests covering knowledge queries, action flows, and error handling.

### Automated Evaluation Suite
The `evaluation/` folder contains a programmatic test runner with **16 test cases** that send real HTTP requests to the `/chat` API endpoint. See [evaluation/evaluation_result.md](evaluation/evaluation_result.md) for detailed results.

```bash
# Start server first, then run evaluation:
cd src && python -m uvicorn app:app --port 8000
python evaluation/evaluation.py                   # Run all 16 tests
python evaluation/evaluation.py --phase 1          # Phase 1 only
python evaluation/evaluation.py --test T05         # Single test
```

| Phase | Capability | Tests |
|-------|-----------|-------|
| 1 | Knowledge Base & Safety (RAG QA + Guardrails) | T01–T08 |
| 2 | Action Flows (Multi-turn + Single-turn) | T09–T11 |
| 3 | Error Handling (Invalid Inputs + Edge Cases) | T12–T16 |

### Unit & Integration Tests
The `tests/` folder contains unit tests for intent routing, action handling, and session management:

```bash
cd /path/to/Startdew_Valley_RAG
pytest tests/ -v
```


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

**16 Automated Test Cases across 3 phases:**
- **Phase 1** (Knowledge & Safety): Basic RAG queries (items, crops, friendship), conversation memory, off-topic rejection, unknown intent, out-of-KB graceful degradation
- **Phase 2** (Action Flows): Friendship plan (3 params), farm plan (2 params), save favorites (auto-complete)
- **Phase 3** (Error Handling): Invalid hearts, invalid budget, invalid/misspelled villager names

## Setup & Installation

**For complete step-by-step installation and running instructions, see [SETUP.md](SETUP.md).**

This includes prerequisites, all 7 installation steps, running tests, troubleshooting, and API reference.

### **Demo**

[![Alt Text](https://github.com/user-attachments/assets/2c7e2a57-214b-44ca-ad87-e87d1da9d1e0)](https://www.youtube.com/watch?v=kNa_qY4sOPI)

## Deployment

### How to start the public demo

**Terminal 1 — Start server:**
```bash
cd src
python -m uvicorn app:app --port 8001
```

**Terminal 2 — Start ngrok:**
```bash
ngrok http 8001
```

Copy the `Forwarding` URL and share it with anyone who needs access.

**Password:** `stardew2026`

### Notes
- Both terminals must stay open while the demo is running
- The ngrok URL changes every time ngrok restarts
- Do not let your computer sleep during the presentation