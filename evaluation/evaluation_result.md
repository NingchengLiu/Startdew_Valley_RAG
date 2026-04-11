# Agent Evaluation Report
**RSM8430 — Team 16 | Stardew Valley RAG Conversational Agent**

---

## Summary

We designed and ran an automated evaluation suite of **16 test cases** against the live agent, covering knowledge retrieval, action flows, error handling, and guardrails. Tests were executed programmatically via the `/chat` API endpoint — no manual UI interaction required.

| Phase | Capability | Passed | Total | Score |
|-------|-----------|--------|-------|-------|
| 1 | Knowledge Base & Safety | 7 | 9 | 77.8% |
| 2 | Action Flows | 3 | 3 | 100% |
| 3 | Error Handling | 4 | 4 | 100% |
| **Overall** | | **14** | **16** | **87.5%** |

---

## Testing Approach

We followed a two-phase testing approach.

**Phase 1 — Manual UI Testing:** Before writing any evaluation code, we manually validated core functionality using a UI testing guide covering 10 scenarios in the browser. This allowed us to quickly verify that basic RAG queries, multi-turn actions, and error handling worked as expected end-to-end. Manual testing also surfaced a subtle failure that would have been difficult to discover through automated checks alone: when asked what crops to grow as gifts for Penny, the agent incorrectly excluded Poppy — one of Penny's specific loved gifts — by misapplying a universal flower rule. This observation became the basis for T06 in the automated suite.

**Phase 2 — Automated Evaluation:** Once the system was stable, we built a programmatic test runner () that sends real HTTP requests to the  endpoint, passes full conversation history across turns, and validates each response against a defined set of checks. This enabled repeatable, objective measurement across 16 test cases — including edge cases and error conditions that would be tedious to verify manually each time.

The two approaches are complementary: manual testing is better for discovering unexpected failures through human observation, while automated testing is better for consistent, quantifiable measurement across a broader set of scenarios.

---

## Methodology

Each test case defines a conversation (1–4 turns) and a set of per-turn checks. The runner sends real HTTP requests, passes full conversation history on each turn, and validates the response fields (`answer`, `intent_type`, `action_in_progress`, `action_result`, `sources`). Ground truths were sourced directly from the official Stardew Valley Wiki.

Check types used:
- `answer_contains` — all listed keywords must appear (strict)
- `answer_contains_any` — at least one keyword must appear (flexible, used when LLM phrasing varies)
- `intent_match` — intent classification must match expected value
- `sources_non_empty` — RAG must return at least one cited source
- `action_completed` / `action_started` / `action_still_active` — action state machine transitions
- `params_correct` — collected parameters must match expected values exactly
- `fuzzy_matched` — corrected villager names must appear in response

---

## Results by Test

### Phase 1 — Knowledge Base & Safety

| ID | Test | Result | Key Check |
|----|------|--------|-----------|
| T01 | Amethyst location (Items intent) | ✅ | Found: mine, gem, amethyst |
| T02 | Cauliflower growth time (Crops intent) | ✅ | "12" present + growth words |
| T03 | Penny's loved gifts (Friendship intent) | ❌ | No specific gift names found |
| T04 | Conversation memory (follow-up without topic) | ✅ | Context words retained |
| T05 | Off-topic rejection (capital of France) | ✅ | Redirected, 0 sources returned |
| T06 | Mixed-intent query — Penny + crops (known limitation) | ❌ | "poppy" missing from answer |
| T07 | General query — how to reach desert | ✅ | bus, desert mentioned |
| T08 | Out-of-KB query — cheat codes | ✅ | No hallucinated cheat code |
| T16 | 3 sequential unrelated questions in same session | ✅ | All 3 answered correctly |

### Phase 2 — Action Flows

| ID | Test | Result | Key Check |
|----|------|--------|-----------|
| T09 | Friendship plan — Elliott, 3 turns | ✅ | Params correct, action completed |
| T10 | Farm plan — 8 plots, 2000g, 2 turns | ✅ | Params correct, action completed |
| T11 | Save favorites — Harvey & Leah, single turn | ✅ | Correct gifts returned |

### Phase 3 — Error Handling

| ID | Test | Result | Key Check |
|----|------|--------|-----------|
| T12 | Invalid heart level (20) → corrected to 4 | ✅ | Error shown, action stays active |
| T13 | Invalid budget (-500) → corrected to 4000 | ✅ | Error shown, action completes |
| T14 | Completely invalid villager names (Gandalf, Hermione) | ✅ | Handled gracefully, no crash |
| T15 | Misspelled names — fuzzy matching | ✅ | "Emly"→Emily, "Shain"→Shane |

---

## Failure Analysis

### T03 — Penny's Loved Gifts (Friendship RAG)

**Query:** *"What gifts does Penny love?"*

The agent correctly identified the intent as `friendship` and returned 3 sources, but the answer did not mention any of Penny's specific loved gifts (Emerald, Melon, Poppy, Diamond, Sandfish, etc.). The RAG retrieval returned chunks about general gifting mechanics rather than Penny's individual gift preference table.

**Root cause:** The FAISS index retrieved general friendship/gifting chunks instead of Penny's character-specific section. This is a **retrieval precision issue** — the query is semantically close to general gifting content, making it hard to surface the correct chunk.

---

### T06 — Mixed Intent Query: Crops + Friendship (Known Limitation)

**Query:** *"What crops should I grow to give as gifts to Penny?"*

The agent answered with general flower/crop recommendations but **incorrectly excluded Poppy**, stating that Penny does not like flowers — when in fact Poppy is one of Penny's specific loved gifts. The wiki explicitly overrides the universal flower rule for Penny.

**Root cause:** The query spans two intents (CROPS + FRIENDSHIP). The orchestrator routed to a single agent, which retrieved generic "universally liked flowers" chunks rather than Penny's individual gift table. The LLM then misapplied the universal rule without finding the individual exception.

**Note:** This failure is intermittent — on some runs the agent retrieves the correct chunk and answers correctly. This non-determinism is itself a finding: **the system's reliability on cross-intent queries depends on which chunks are retrieved in a given run.**

---

## Key Findings

**What works well:**
- Intent classification is reliable across all 3 categories (crops, items, friendship)
- Multi-turn action flows work correctly — parameter collection, validation, and state management all function as designed
- Error handling is robust — invalid inputs are caught and re-asked gracefully
- Fuzzy villager name matching handles common misspellings
- Sequential questions in the same session do not bleed context into each other

**System limitations identified:**
- **RAG retrieval precision for character-specific data:** When a villager's individual gift preference overrides a universal rule, the system may retrieve the universal rule chunk instead of the character-specific one. This affects both T03 and T06.
- **Cross-intent queries:** Queries that span multiple intent categories (e.g., crops AND friendship simultaneously) are handled by a single-intent router, which may surface incomplete information.
- **LLM non-determinism:** The same query can produce different answers across runs, making certain failure modes intermittent rather than consistent.

---

## Running the Evaluation

```bash
# Terminal 1: start server
cd src2 && python -m uvicorn app:app --port 8000

# Terminal 2: run all tests
cd evaluation && python evaluation.py --output results.json

# Run a single test
python evaluation.py --test T06

# Run by phase
python evaluation.py --phase 3
```