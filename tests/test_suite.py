"""
test_suite.py — Comprehensive evaluation test suite for the conversational agent.

Tests cover:
- Intent routing accuracy
- Knowledge retrieval
- Action execution
- Multi-turn conversations
- Error handling
- Out-of-scope rejection
"""

import sys
from pathlib import Path
from enum import Enum
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator import route_intent, IntentType
from actions import get_action_handler, ActionContext, ActionType
from session_manager import get_session_manager, SessionState


class TestResult(Enum):
    """Test outcome."""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"


class TestCase:
    """Individual test case."""
    
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.result = None
        self.details = ""
    
    def run(self) -> bool:
        """Run test and return True if passed."""
        raise NotImplementedError
    
    def __str__(self):
        return f"{self.result.value} | {self.category:20s} | {self.name}"


# ── INTENT ROUTING TESTS ───────────────────────────────────────────────────────

class TestFriendshipIntent(TestCase):
    """Test friendship intent detection."""
    def __init__(self):
        super().__init__("Friendship queries route to FRIENDSHIP", "Intent Routing")
    
    def run(self) -> bool:
        queries = [
            "How do I marry Abigail?",
            "What does Sebastian like?",
            "How to increase hearts with Haley?",
        ]
        results = []
        for q in queries:
            intent = route_intent(q)
            results.append(intent.intent_type == IntentType.FRIENDSHIP)
        
        self.result = TestResult.PASS if all(results) else TestResult.FAIL
        self.details = f"Routed {sum(results)}/{len(results)} correctly"
        return all(results)


class TestCropIntent(TestCase):
    """Test crop/farming intent detection."""
    def __init__(self):
        super().__init__("Crop queries route to CROPS", "Intent Routing")
    
    def run(self) -> bool:
        queries = [
            "What crops should I plant in spring?",
            "How long does cauliflower take?",
            "Most profitable summer crop?",
        ]
        results = []
        for q in queries:
            intent = route_intent(q)
            results.append(intent.intent_type == IntentType.CROPS)
        
        self.result = TestResult.PASS if all(results) else TestResult.FAIL
        self.details = f"Routed {sum(results)}/{len(results)} correctly"
        return all(results)


class TestItemIntent(TestCase):
    """Test item/resource intent detection."""
    def __init__(self):
        super().__init__("Item queries route to ITEMS", "Intent Routing")
    
    def run(self) -> bool:
        queries = [
            "How do I craft a chest?",
            "Where can I find copper?",
            "What's the fishing rod recipe?",
        ]
        results = []
        for q in queries:
            intent = route_intent(q)
            results.append(intent.intent_type == IntentType.ITEMS)
        
        self.result = TestResult.PASS if all(results) else TestResult.FAIL
        self.details = f"Routed {sum(results)}/{len(results)} correctly"
        return all(results)


class TestOffTopicDetection(TestCase):
    """Test off-topic question rejection."""
    def __init__(self):
        super().__init__("Off-topic queries rejected as OFF_TOPIC", "Guardrails")
    
    def run(self) -> bool:
        queries = [
            "What's the weather today?",
            "Tell me about politics",
            "How do I cook pasta?",
        ]
        results = []
        for q in queries:
            intent = route_intent(q)
            results.append(intent.intent_type == IntentType.OFF_TOPIC)
        
        self.result = TestResult.PASS if all(results) else TestResult.FAIL
        self.details = f"Rejected {sum(results)}/{len(results)} correctly"
        return all(results)


class TestUnknownIntent(TestCase):
    """Test unknown/ambiguous queries."""
    def __init__(self):
        super().__init__("Ambiguous queries classified as UNKNOWN", "Intent Routing")
    
    def run(self) -> bool:
        queries = [
            "Tell me about Stardew Valley",
            "What can you tell me about the game?",
        ]
        results = []
        for q in queries:
            intent = route_intent(q)
            results.append(intent.intent_type == IntentType.UNKNOWN)
        
        self.result = TestResult.PASS if all(results) else TestResult.FAIL
        self.details = f"Classified {sum(results)}/{len(results)} correctly"
        return all(results)


# ── ACTION TESTS ───────────────────────────────────────────────────────────────

class TestActionDetection(TestCase):
    """Test action intent detection."""
    def __init__(self):
        super().__init__("Action requests detected correctly", "Actions")
    
    def run(self) -> bool:
        handler = get_action_handler()
        
        # Test friendship plan detection
        msg = "Help me create a friendship plan"
        action = handler.detect_action_intent(msg)
        friendship_detected = action == ActionType.CREATE_FRIENDSHIP_PLAN
        
        # Test farm plan detection
        msg = "Plan my farm"
        action = handler.detect_action_intent(msg)
        farm_detected = action == ActionType.CREATE_FARM_PLAN
        
        # Test save favorites detection
        msg = "Save Abigail's favorites"
        action = handler.detect_action_intent(msg)
        save_detected = action == ActionType.SAVE_FAVORITES
        
        success = friendship_detected and farm_detected and save_detected
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Friendship: {friendship_detected}, Farm: {farm_detected}, Save: {save_detected}"
        return success


class TestMultiTurnFriendshipPlan(TestCase):
    """Test multi-turn friendship plan creation."""
    def __init__(self):
        super().__init__("Multi-turn friendship plan collection", "Actions")
    
    def run(self) -> bool:
        handler = get_action_handler()
        ctx = ActionContext(action_type=ActionType.CREATE_FRIENDSHIP_PLAN)
        
        # Collect parameters across turns
        success1, _ = handler.collect_parameter(ctx, "Abigail")
        success2, _ = handler.collect_parameter(ctx, "2")
        success3, _ = handler.collect_parameter(ctx, "3")
        
        # Execute
        result = handler.execute_action(ctx)
        
        success = success1 and success2 and success3 and result.success
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Params collected: {[success1, success2, success3]}, Executed: {result.success}"
        return success


class TestMultiTurnFarmPlan(TestCase):
    """Test multi-turn farm plan creation."""
    def __init__(self):
        super().__init__("Multi-turn farm plan collection", "Actions")
    
    def run(self) -> bool:
        handler = get_action_handler()
        ctx = ActionContext(action_type=ActionType.CREATE_FARM_PLAN)
        
        # Collect parameters
        success1, _ = handler.collect_parameter(ctx, "20")
        success2, _ = handler.collect_parameter(ctx, "5000")
        
        # Execute
        result = handler.execute_action(ctx)
        
        success = success1 and success2 and result.success
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Params collected: {[success1, success2]}, Executed: {result.success}"
        return success


class TestActionValidation(TestCase):
    """Test action parameter validation."""
    def __init__(self):
        super().__init__("Action parameter validation", "Actions")
    
    def run(self) -> bool:
        handler = get_action_handler()
        ctx = ActionContext(action_type=ActionType.CREATE_FRIENDSHIP_PLAN)
        
        # Test invalid villager
        success1, _ = handler.collect_parameter(ctx, "InvalidVillager")
        
        # Test valid villager
        success2, _ = handler.collect_parameter(ctx, "Sebastian")
        
        # Test invalid hearts
        success3, _ = handler.collect_parameter(ctx, "15")  # Out of range
        
        # Test valid hearts
        success4, _ = handler.collect_parameter(ctx, "5")
        
        # Invalid and valid should fail/succeed correctly
        valid_validation = not success1 and success2 and not success3 and success4
        self.result = TestResult.PASS if valid_validation else TestResult.FAIL
        self.details = f"Validations: Invalid rejected {not success1}, Valid accepted {success2}"
        return valid_validation


# ── CONVERSATION MEMORY TESTS ──────────────────────────────────────────────────

class TestSessionCreation(TestCase):
    """Test session creation."""
    def __init__(self):
        super().__init__("Session creation and retrieval", "Memory")
    
    def run(self) -> bool:
        manager = get_session_manager()
        session = manager.create_session("user123", "sess_abc")
        
        retrieved = manager.get_session("sess_abc")
        success = retrieved is not None and retrieved.user_id == "user123"
        
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Session created and retrieved: {success}"
        return success


class TestConversationHistory(TestCase):
    """Test conversation history tracking."""
    def __init__(self):
        super().__init__("Conversation history tracking", "Memory")
    
    def run(self) -> bool:
        manager = get_session_manager()
        session = manager.create_session("user456", "sess_def")
        
        # Add messages
        manager.add_user_message("sess_def", "How do I marry Abigail?", "FRIENDSHIP")
        manager.add_assistant_message("sess_def", "Here's how to marry Abigail...", "FRIENDSHIP")
        
        # Retrieve history
        history = manager.get_conversation_history("sess_def")
        
        success = len(history) == 2 and history[0]["role"] == "user" and history[1]["role"] == "assistant"
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Messages stored and retrieved: {len(history)}"
        return success


class TestContextReference(TestCase):
    """Test context window retrieval."""
    def __init__(self):
        super().__init__("Context window for memory reference", "Memory")
    
    def run(self) -> bool:
        manager = get_session_manager()
        session = manager.create_session("user789", "sess_ghi")
        
        # Add conversation
        manager.add_user_message("sess_ghi", "How do I increase hearts with Abigail?")
        manager.add_assistant_message("sess_ghi", "Gift her regularly...")
        manager.add_user_message("sess_ghi", "What's her birthday?")
        
        # Get context
        context = manager.get_context("sess_ghi")
        
        success = "Abigail" in context and "birthday" in context
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Context retrieved with {len(context)} chars"
        return success


# ── ERROR HANDLING TESTS ───────────────────────────────────────────────────────

class TestInvalidInput(TestCase):
    """Test handling of invalid input."""
    def __init__(self):
        super().__init__("Invalid input handling", "Error Handling")
    
    def run(self) -> bool:
        handler = get_action_handler()
        ctx = ActionContext(action_type=ActionType.CREATE_FRIENDSHIP_PLAN)
        
        # Try invalid input
        success, message = handler.collect_parameter(ctx, "NotANumber")
        
        # Should reject and provide message
        valid_error = not success and "don't recognize" in message.lower()
        self.result = TestResult.PASS if valid_error else TestResult.FAIL
        self.details = f"Invalid input rejected with error message"
        return valid_error


class TestEmptyQuery(TestCase):
    """Test handling of empty queries."""
    def __init__(self):
        super().__init__("Empty query handling", "Error Handling")
    
    def run(self) -> bool:
        intent = route_intent("")
        
        # Should classify as UNKNOWN or OFF_TOPIC
        success = intent.intent_type in [IntentType.UNKNOWN, IntentType.OFF_TOPIC]
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"Empty query classified as {intent.intent_type.value}"
        return success


class TestCaseSensitivity(TestCase):
    """Test case-insensitive routing."""
    def __init__(self):
        super().__init__("Case-insensitive routing", "Error Handling")
    
    def run(self) -> bool:
        queries = [
            "how do i marry abigail?",
            "HOW DO I MARRY ABIGAIL?",
            "How Do I Marry Abigail?",
        ]
        results = [route_intent(q).intent_type for q in queries]
        
        success = all(r == IntentType.FRIENDSHIP for r in results)
        self.result = TestResult.PASS if success else TestResult.FAIL
        self.details = f"All case variants routed consistently"
        return success


# ── Test Suite Runner ──────────────────────────────────────────────────────────

def run_test_suite() -> Dict[str, Any]:
    """Run all tests and generate report."""
    test_cases = [
        # Intent routing
        TestFriendshipIntent(),
        TestCropIntent(),
        TestItemIntent(),
        TestOffTopicDetection(),
        TestUnknownIntent(),
        
        # Actions
        TestActionDetection(),
        TestMultiTurnFriendshipPlan(),
        TestMultiTurnFarmPlan(),
        TestActionValidation(),
        
        # Conversation memory
        TestSessionCreation(),
        TestConversationHistory(),
        TestContextReference(),
        
        # Error handling
        TestInvalidInput(),
        TestEmptyQuery(),
        TestCaseSensitivity(),
    ]
    
    print("=" * 80)
    print("STARDEW VALLEY AGENT — EVALUATION TEST SUITE")
    print("=" * 80)
    print()
    
    results_by_category = {}
    total_passed = 0
    
    for test in test_cases:
        passed = test.run()
        if passed:
            total_passed += 1
        
        print(test)
        print(f"  Details: {test.details}")
        print()
        
        # Track by category
        if test.category not in results_by_category:
            results_by_category[test.category] = {"passed": 0, "total": 0}
        results_by_category[test.category]["total"] += 1
        if passed:
            results_by_category[test.category]["passed"] += 1
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total: {total_passed}/{len(test_cases)} tests passed ({100*total_passed//len(test_cases)}%)")
    print()
    print("By Category:")
    for category, stats in results_by_category.items():
        pct = 100 * stats["passed"] // stats["total"]
        print(f"  {category:20s}: {stats['passed']}/{stats['total']} ({pct}%)")
    
    print()
    print("=" * 80)
    
    return {
        "total_tests": len(test_cases),
        "passed": total_passed,
        "failed": len(test_cases) - total_passed,
        "accuracy": total_passed / len(test_cases),
        "by_category": results_by_category
    }


if __name__ == "__main__":
    from typing import Dict, Any
    report = run_test_suite()
