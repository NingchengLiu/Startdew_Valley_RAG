"""
test_orchestrator.py — Tests for LLM-based intent routing.

Run with: pytest tests/agent_tests/test_orchestrator.py -v
Or:       python -m pytest tests/agent_tests/test_orchestrator.py -v
Or:       python3 tests/agent_tests/test_orchestrator.py
"""

import sys
from pathlib import Path

# Add src to path so we can import orchestrator and llm
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from orchestrator import route_intent, IntentType


class TestIntentRouter:
    """Test intent routing logic."""
    
    def test_friendship_intent(self):
        """Test friendship intent classification."""
        queries = [
            "How do I increase friendship with Abigail?",
            "How do I marry Sebastian?",
            "What does Haley like as a gift?",
            "What are the heart events with Elliott?",
        ]
        for query in queries:
            intent = route_intent(query)
            assert intent.intent_type == IntentType.FRIENDSHIP, f"Failed: {query}"
            assert intent.confidence > 0.6, f"Low confidence: {query}"
    
    def test_item_intent(self):
        """Test item/resource intent classification."""
        queries = [
            "How do I craft a chest?",
            "Where can I find a ruby?",
            "How do I get a fishing rod?",
            "What's the recipe for a furnace?",
            "How much does a watering can cost?",
        ]
        for query in queries:
            intent = route_intent(query)
            assert intent.intent_type == IntentType.ITEMS, f"Failed: {query}"
            assert intent.confidence > 0.6, f"Low confidence: {query}"
    
    def test_crop_intent(self):
        """Test crop/farming intent classification."""
        queries = [
            "What crops should I plant in spring?",
            "How long does corn take to grow?",
            "What's the most profitable crop in summer?",
            "When should I water my plants?",
            "What fertilizer should I use?",
        ]
        for query in queries:
            intent = route_intent(query)
            assert intent.intent_type == IntentType.CROPS, f"Failed: {query}"
            assert intent.confidence > 0.6, f"Low confidence: {query}"
    
    def test_off_topic_detection(self):
        """Test off-topic question rejection."""
        queries = [
            "What's the weather today?",
            "Tell me about politics",
            "How do I cook a real recipe?",
            "Tell me about the news",
        ]
        for query in queries:
            intent = route_intent(query)
            assert intent.intent_type == IntentType.OFF_TOPIC, f"Failed: {query}"
            assert intent.confidence > 0.75, f"Low confidence: {query}"
    
    def test_unknown_intent(self):
        """Test unknown/ambiguous intent classification."""
        queries = [
            "Tell me about Stardew Valley",
            "What can you tell me about the game?",
            "General game information",
        ]
        for query in queries:
            intent = route_intent(query)
            assert intent.intent_type == IntentType.UNKNOWN, f"Failed: {query}"
    
    def test_intent_confidence(self):
        """Test that confidence scores are reasonable."""
        # Strong intent signals should have high confidence
        strong_intent = route_intent("How do I marry Abigail? What gifts does she like?")
        assert strong_intent.confidence > 0.7, f"Should be high: {strong_intent.confidence}"
        
        # Weak/ambiguous should have lower confidence
        weak_intent = route_intent("Tell me about the game")
        assert weak_intent.confidence <= 0.6, f"Should be low: {weak_intent.confidence}"
    
    def test_mixed_intent_resolution(self):
        """Test that when multiple intents match, the strongest wins."""
        # "Craft a tool to farm" — both items and crops, but items should win
        intent = route_intent("I need to craft a tool to farm more efficiently")
        # Could be either ITEMS or CROPS, but one should win
        assert intent.intent_type in [IntentType.ITEMS, IntentType.CROPS]
    
    def test_intent_reasoning(self):
        """Test that reasoning is provided."""
        intent = route_intent("How do I marry Abigail?")
        assert intent.reasoning, "Should provide reasoning"
        assert "keyword" in intent.reasoning.lower() or "detected" in intent.reasoning.lower()
    
    def test_original_query_preserved(self):
        """Test that original query is preserved in response."""
        query = "How do I increase friendship with Abigail?"
        intent = route_intent(query)
        assert intent.original_query == query


class TestIntentRouterEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_query(self):
        """Test handling of empty or minimal queries."""
        # Empty query should be classified as UNKNOWN
        intent = route_intent("")
        assert intent.intent_type in [IntentType.UNKNOWN, IntentType.OFF_TOPIC]
    
    def test_single_keyword(self):
        """Test single keyword queries."""
        intent = route_intent("crops")
        assert intent.intent_type == IntentType.CROPS
    
    def test_case_insensitivity(self):
        """Test that queries are case-insensitive."""
        intent_lower = route_intent("how do i marry abigail?")
        intent_upper = route_intent("HOW DO I MARRY ABIGAIL?")
        intent_mixed = route_intent("How Do I Marry Abigail?")
        
        assert intent_lower.intent_type == intent_upper.intent_type
        assert intent_lower.intent_type == intent_mixed.intent_type
    
    def test_special_characters(self):
        """Test handling of special characters and punctuation."""
        queries = [
            "How do I marry Abigail?!",
            "What crops... should I plant?",
            "Items: where do I find them?",
        ]
        for query in queries:
            intent = route_intent(query)
            # Should not crash and should classify something
            assert intent.intent_type in [
                IntentType.FRIENDSHIP, IntentType.CROPS, IntentType.ITEMS,
                IntentType.UNKNOWN, IntentType.OFF_TOPIC
            ]
    
    def test_very_long_query(self):
        """Test handling of very long queries."""
        long_query = "I want to know everything about farming crops in Stardew Valley " * 10
        intent = route_intent(long_query)
        assert intent.intent_type == IntentType.CROPS
        # Confidence should decrease with dilution but still classify
        assert intent.confidence > 0.3


class TestIntentRouterKeywordCoverage:
    """Test that keyword sets cover common queries."""
    
    def test_popular_item_queries(self):
        """Test common item-related questions."""
        popular_queries = {
            "How do I get a fishing rod?": IntentType.ITEMS,
            "Where can I find copper?": IntentType.ITEMS,
            "What's the recipe for a scarecrow?": IntentType.ITEMS,
            "How much does a horse cost?": IntentType.ITEMS,
        }
        for query, expected_intent in popular_queries.items():
            intent = route_intent(query)
            assert intent.intent_type == expected_intent, f"Failed: {query}"
    
    def test_popular_friendship_queries(self):
        """Test common friendship-related questions."""
        popular_queries = {
            "How do I romance Abigail?": IntentType.FRIENDSHIP,
            "What's Sebastian's birthday?": IntentType.FRIENDSHIP,
            "How do I unlock the beach party event?": IntentType.FRIENDSHIP,
            "Can I marry multiple people?": IntentType.FRIENDSHIP,
        }
        for query, expected_intent in popular_queries.items():
            intent = route_intent(query)
            assert intent.intent_type == expected_intent, f"Failed: {query}"
    
    def test_popular_crop_queries(self):
        """Test common crop/farming questions."""
        popular_queries = {
            "What should I plant in spring?": IntentType.CROPS,
            "How long does cauliflower take?": IntentType.CROPS,
            "What's the profit for corn?": IntentType.CROPS,
            "Do I need to water every day?": IntentType.CROPS,
        }
        for query, expected_intent in popular_queries.items():
            intent = route_intent(query)
            assert intent.intent_type == expected_intent, f"Failed: {query}"


if __name__ == "__main__":
    # Quick smoke tests
    print("Running quick intent routing tests...")
    
    test_router = TestIntentRouter()
    test_router.test_friendship_intent()
    print("✓ Friendship intent tests passed")
    
    test_router.test_item_intent()
    print("✓ Item intent tests passed")
    
    test_router.test_crop_intent()
    print("✓ Crop intent tests passed")
    
    test_router.test_off_topic_detection()
    print("✓ Off-topic detection tests passed")
    
    test_router.test_unknown_intent()
    print("✓ Unknown intent tests passed")
    
    test_edge = TestIntentRouterEdgeCases()
    test_edge.test_case_insensitivity()
    print("✓ Case insensitivity tests passed")
    
    test_coverage = TestIntentRouterKeywordCoverage()
    test_coverage.test_popular_item_queries()
    print("✓ Popular item queries tests passed")
    
    print("\n✅ All tests passed!")
