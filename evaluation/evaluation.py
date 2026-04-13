"""
evaluation.py — Automated evaluation suite for the Stardew Valley RAG Agent.

Loads test cases from test_cases.json and runs them against the live API.

Usage
-----
    # Start server first:
    # cd src && python -m uvicorn app:app --port 8000

    python evaluation.py                          # Run all tests
    python evaluation.py --phase 1                # Phase 1 only
    python evaluation.py --phase 2                # Phase 2 only
    python evaluation.py --phase 3                # Phase 3 only
    python evaluation.py --test T05               # Single test by ID
    python evaluation.py --output results.json    # Save JSON report
    python evaluation.py --base-url http://...    # Custom server URL

Requirements
------------
    pip install requests
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
import sys
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
from pathlib import Path

import requests

# ── Config ─────────────────────────────────────────────────────────────────────

DEFAULT_BASE_URL   = "http://localhost:8000"
DEFAULT_CASES_FILE = Path(__file__).parent / "test_cases.json"
CHAT_ENDPOINT      = "/chat"
HEALTH_ENDPOINT    = "/health"
REQUEST_TIMEOUT    = 60


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name:   str
    passed: bool
    detail: str = ""


@dataclass
class TestResult:
    test_id:      str
    name:         str
    phase:        int
    capability:   str
    passed:       bool
    score:        float
    checks:       list
    turns_run:    int
    error:        Optional[str]
    duration_ms:  float
    ground_truth: str
    notes:        str


@dataclass
class EvalReport:
    timestamp:        str
    base_url:         str
    total_tests:      int
    passed:           int
    failed:           int
    overall_score:    float
    phase_scores:     dict
    results:          list
    failure_analysis: list


# ── HTTP client ────────────────────────────────────────────────────────────────

class AgentClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self) -> dict:
        r = requests.get(f"{self.base_url}{HEALTH_ENDPOINT}", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def chat(self, query: str, session_id: str,
             history: Optional[list] = None) -> tuple:
        payload = {
            "query": query,
            "session_id": session_id,
            "conversation_history": history or [],
            "top_k": 3,
        }
        t0 = time.perf_counter()
        r = requests.post(
            f"{self.base_url}{CHAT_ENDPOINT}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        return r.json(), elapsed_ms


# ── Check evaluators ───────────────────────────────────────────────────────────

def evaluate_turn_checks(checks: dict, response: dict,
                          all_responses: list) -> list:
    """
    Evaluate all checks for a single turn response.

    Supported check keys:
        answer_contains          — list[str]: ALL must appear in answer
        answer_contains_any      — list[str]: at least ONE must appear
        answer_does_not_contain  — list[str]: NONE must appear
        answer_non_empty         — bool
        sources_non_empty        — bool
        sources_empty            — bool
        intent_match             — str: exact match on intent_type
        action_started           — bool: action_in_progress == True
        action_still_active      — bool: action_in_progress == True
        action_completed         — bool: action_in_progress == False
        action_result_present    — bool: action_result is non-null
        params_correct           — dict: expected {key: value} in parameters
        params_include_villagers — list[str]: expected villager names in params
        context_maintained       — bool: heuristic topic-word overlap
        fuzzy_matched            — list[str]: corrected names appear in answer
    """
    results = []
    answer   = response.get("answer", "").lower()
    sources  = response.get("sources", [])
    intent   = response.get("intent_type", "").lower()
    in_prog  = response.get("action_in_progress", False)
    ar       = response.get("action_result") or {}

    for check_name, expected in checks.items():

        if check_name == "answer_contains":
            words   = [w.lower() for w in expected]
            missing = [w for w in words if w not in answer]
            passed  = len(missing) == 0
            results.append(CheckResult(check_name, passed,
                f"Missing: {missing}" if not passed else "OK"))

        elif check_name == "answer_contains_any":
            words = [w.lower() for w in expected]
            found = [w for w in words if w in answer]
            passed = len(found) > 0
            results.append(CheckResult(check_name, passed,
                f"Found: {found}" if passed else f"None of {words} found"))

        elif check_name == "answer_does_not_contain":
            words = [w.lower() for w in expected]
            found = [w for w in words if w in answer]
            passed = len(found) == 0
            results.append(CheckResult(check_name, passed,
                f"Forbidden words found: {found}" if not passed else "OK"))

        elif check_name == "answer_non_empty":
            passed = bool(answer.strip())
            results.append(CheckResult(check_name, passed,
                "Answer is empty" if not passed else "OK"))

        elif check_name == "sources_non_empty":
            passed = len(sources) > 0
            results.append(CheckResult(check_name, passed,
                f"Got {len(sources)} source(s)"))

        elif check_name == "sources_empty":
            passed = len(sources) == 0
            results.append(CheckResult(check_name, passed,
                f"Expected 0 sources, got {len(sources)}"))

        elif check_name == "intent_match":
            passed = intent == expected.lower()
            results.append(CheckResult(check_name, passed,
                f"Expected '{expected}', got '{intent}'"))

        elif check_name in ("action_started", "action_still_active"):
            passed = in_prog is True
            results.append(CheckResult(check_name, passed,
                f"action_in_progress={in_prog}"))

        elif check_name == "action_completed":
            passed = in_prog is False
            results.append(CheckResult(check_name, passed,
                f"action_in_progress={in_prog}"))

        elif check_name == "action_result_present":
            passed = bool(ar)
            results.append(CheckResult(check_name, passed,
                "present" if passed else "action_result missing"))

        elif check_name == "params_correct":
            params = ar.get("parameters", {})
            failures = []
            for k, v in expected.items():
                actual = params.get(k)
                if str(actual).lower() != str(v).lower():
                    failures.append(f"{k}: expected={v}, got={actual}")
            passed = len(failures) == 0
            results.append(CheckResult(check_name, passed,
                ", ".join(failures) if failures else "OK"))

        elif check_name == "params_include_villagers":
            params    = ar.get("parameters", {})
            saved     = [v.lower() for v in params.get("villagers", [])]
            exp_lower = [v.lower() for v in expected]
            missing   = [v for v in exp_lower if v not in saved]
            passed    = len(missing) == 0
            results.append(CheckResult(check_name, passed,
                f"Missing: {missing}" if not passed else f"Found: {saved}"))

        elif check_name == "context_maintained":
            topic_words = {
                "day", "days", "grow", "week", "spring", "summer", "fall",
                "winter", "crop", "crops", "plant", "harvest", "profit", "gold",
                "parsnip", "cauliflower", "potato", "starfruit", "blueberry",
                "strawberry", "melon", "pumpkin",
            }
            overlap = topic_words & set(answer.split())
            passed  = len(overlap) > 0
            results.append(CheckResult(check_name, passed,
                f"Topic words found: {overlap}" if passed
                else "No topic words in follow-up answer"))

        elif check_name == "fuzzy_matched":
            exp_lower = [v.lower() for v in expected]
            found     = [v for v in exp_lower if v in answer]
            passed    = len(found) == len(exp_lower)
            results.append(CheckResult(check_name, passed,
                f"Matched: {found} / Expected: {exp_lower}"))

    return results


# ── Test runner ────────────────────────────────────────────────────────────────

class TestRunner:

    def __init__(self, client: AgentClient):
        self.client = client

    def _new_session(self) -> str:
        return f"eval-{uuid.uuid4().hex[:8]}"

    def _build_history(self, turns_def: list, responses: list) -> list:
        history = []
        for i, turn in enumerate(turns_def):
            history.append({"role": "user",      "content": turn["user"]})
            history.append({"role": "assistant",  "content": responses[i].get("answer", "")})
        return history

    def run_test(self, tc: dict) -> TestResult:
        test_id    = tc["id"]
        capability = tc.get("capability", test_id)
        phase      = tc["phase"]
        turns_def  = tc["turns"]
        t0         = time.perf_counter()

        try:
            sid       = self._new_session()
            responses = []
            all_checks: list = []

            for turn_idx, turn in enumerate(turns_def):
                query      = turn["user"]
                checks_def = turn.get("checks", {})

                history = self._build_history(turns_def[:turn_idx], responses)
                resp, _ = self.client.chat(query, sid, history)
                responses.append(resp)

                turn_checks = evaluate_turn_checks(checks_def, resp, responses)
                for c in turn_checks:
                    c.name = f"turn{turn_idx+1}_{c.name}"
                all_checks.extend(turn_checks)

            passed = all(c.passed for c in all_checks)
            score  = round(sum(c.passed for c in all_checks) / max(len(all_checks), 1), 3)

            return TestResult(
                test_id=test_id, name=capability, phase=phase,
                capability=capability, passed=passed, score=score,
                checks=all_checks, turns_run=len(turns_def), error=None,
                duration_ms=round((time.perf_counter() - t0) * 1000, 1),
                ground_truth=tc.get("ground_truth", ""),
                notes=tc.get("notes", ""),
            )

        except Exception as exc:
            return TestResult(
                test_id=test_id, name=capability, phase=phase,
                capability=capability, passed=False, score=0.0,
                checks=[], turns_run=0, error=str(exc),
                duration_ms=round((time.perf_counter() - t0) * 1000, 1),
                ground_truth=tc.get("ground_truth", ""),
                notes=tc.get("notes", ""),
            )


# ── Report ─────────────────────────────────────────────────────────────────────

def build_report(results: list, base_url: str) -> EvalReport:
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    phase_scores: dict = {}
    for r in results:
        p = r.phase
        if p not in phase_scores:
            phase_scores[p] = {"passed": 0, "total": 0, "score": 0.0}
        phase_scores[p]["total"] += 1
        if r.passed:
            phase_scores[p]["passed"] += 1
    for p, s in phase_scores.items():
        s["score"] = round(s["passed"] / max(s["total"], 1), 3)

    failures = [
        {
            "test_id":       r.test_id,
            "name":          r.name,
            "phase":         r.phase,
            "capability":    r.capability,
            "failed_checks": [f"{c.name}: {c.detail}" for c in r.checks if not c.passed],
            "error":         r.error,
            "ground_truth":  r.ground_truth,
            "notes":         r.notes,
        }
        for r in results if not r.passed
    ]

    return EvalReport(
        timestamp=datetime.now().isoformat(), base_url=base_url,
        total_tests=len(results), passed=passed, failed=failed,
        overall_score=round(passed / max(len(results), 1), 3),
        phase_scores=phase_scores, results=results,
        failure_analysis=failures,
    )


def print_report(report: EvalReport):
    W = 72
    PHASE_NAMES = {1: "Knowledge Base & Safety", 2: "Action Flows", 3: "Error Handling"}

    print("\n" + "═" * W)
    print("  STARDEW VALLEY RAG AGENT — EVALUATION REPORT")
    print("═" * W)
    print(f"  Timestamp : {report.timestamp}")
    print(f"  Server    : {report.base_url}")
    print(f"  Tests     : {report.total_tests}  |  Passed: {report.passed}  |  Failed: {report.failed}")
    print(f"  Overall   : {report.overall_score * 100:.1f}%")
    print()

    for phase, stats in sorted(report.phase_scores.items()):
        label = PHASE_NAMES.get(phase, f"Phase {phase}")
        bar   = "█" * stats["passed"] + "░" * (stats["total"] - stats["passed"])
        print(f"  Phase {phase} [{label}]")
        print(f"          {bar}  {stats['passed']}/{stats['total']} ({stats['score']*100:.0f}%)")
    print()

    print(f"  {'ID':<6} {'Capability':<38} {'Ph':>3} {'Result':<8} {'Score':>6}  {'ms':>7}")
    print("  " + "─" * (W - 2))
    for r in report.results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        cap    = r.capability[:37]
        print(f"  {r.test_id:<6} {cap:<38} {r.phase:>3} {status:<8} "
              f"{r.score*100:>5.0f}%  {r.duration_ms:>7.0f}")

    if report.failure_analysis:
        print()
        print("  FAILURE ANALYSIS")
        print("  " + "─" * (W - 2))
        for f in report.failure_analysis:
            print(f"\n  [{f['test_id']}] {f['name']}  (Phase {f['phase']})")
            if f["error"]:
                print(f"  ⚠  Exception : {f['error']}")
            for fc in f["failed_checks"]:
                print(f"  ✗  {fc}")
            if f["ground_truth"]:
                gt = f["ground_truth"][:120]
                print(f"  📖 Truth : {gt}")
            if f["notes"]:
                print(f"  ℹ  Notes : {f['notes']}")

    print("\n" + "═" * W + "\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Stardew Valley RAG — Evaluation Suite")
    p.add_argument("--base-url",   default=DEFAULT_BASE_URL)
    p.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE))
    p.add_argument("--phase",      type=int, choices=[1, 2, 3], default=None)
    p.add_argument("--test",       default=None, help="Single test ID, e.g. T05")
    p.add_argument("--output",     default=None, help="Save JSON report to file")
    return p.parse_args()


def main():
    args   = parse_args()
    client = AgentClient(args.base_url)

    print(f"\n[eval] Connecting to {args.base_url} …")
    try:
        h = client.health()
        print(f"[eval] ✅ Server OK  model={h.get('llm_model')}  "
              f"index_size={h.get('index_size')}")
    except Exception as e:
        print(f"[eval] ❌ Server unreachable: {e}")
        sys.exit(1)

    cases_path = Path(args.cases_file)
    if not cases_path.exists():
        print(f"[eval] ❌ Test cases file not found: {cases_path}")
        sys.exit(1)

    with open(cases_path) as f:
        data = json.load(f)
    all_cases = data["test_cases"]

    if args.test:
        all_cases = [tc for tc in all_cases if tc["id"] == args.test]
    elif args.phase:
        all_cases = [tc for tc in all_cases if tc["phase"] == args.phase]

    if not all_cases:
        print("[eval] No matching test cases found.")
        sys.exit(1)

    print(f"[eval] Running {len(all_cases)} test(s) from {cases_path.name}\n")

    runner  = TestRunner(client)
    results = []

    for i, tc in enumerate(all_cases, 1):
        turns = len(tc.get("turns", []))
        print(f"  [{i:>2}/{len(all_cases)}] {tc['id']} — {tc['capability'][:48]} "
              f"({turns} turn{'s' if turns != 1 else ''}) …",
              end=" ", flush=True)
        res = runner.run_test(tc)
        results.append(res)
        bad = [c for c in res.checks if not c.passed]
        print(f"{'✅' if res.passed else '❌'}  "
              f"{res.score*100:.0f}%  ({res.duration_ms:.0f}ms)"
              + (f"  [{len(bad)} failed]" if bad else ""))

    report = build_report(results, args.base_url)
    print_report(report)

    if args.output:
        def to_plain(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: to_plain(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [to_plain(i) for i in obj]
            return obj
        with open(args.output, "w") as f:
            json.dump(to_plain(report), f, indent=2, default=str)
        print(f"[eval] Report saved → {args.output}\n")

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()