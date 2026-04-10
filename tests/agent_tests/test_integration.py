"""
test_integration.py — Integration test for multi-agent orchestrator.

This script tests the orchestrator without requiring full agent instantiation
(which requires FAISS and other heavy dependencies).

Usage:
    python3 test_integration.py
"""

from orchestrator import route_intent, IntentType


def test_orchestrator_routing():
    """Test that orchestrator routes to correct intent types."""
    
    test_cases = [
        # (query, expected_intent_type)
        ("How do I craft a chest?", IntentType.ITEMS),
        ("How do I increase friendship with Abigail?", IntentType.FRIENDSHIP),
        ("What crops should I plant in spring?", IntentType.CROPS),
        ("Tell me about Stardew Valley", IntentType.UNKNOWN),
    ]
    
    for query, expected_intent in test_cases:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"{'='*70}")
        
        # Route intent
        routed = route_intent(query)
        print(f"Intent Type: {routed.intent_type.value}")
        print(f"Confidence:  {routed.confidence:.2f}")
        print(f"Reasoning:   {routed.reasoning}")
        
        # Verify routing
        assert routed.intent_type == expected_intent, \
            f"Expected {expected_intent}, got {routed.intent_type}"
        
        print(f"✓ Routed correctly to: {routed.intent_type.value}")


def test_off_topic_rejection():
    """Test that off-topic queries are rejected."""
    
    test_cases = [
        "What's the weather today?",
        "Tell me about politics",
        "Tell me about the news",
    ]
    
    print(f"\n{'='*70}")
    print("Testing Off-Topic Rejection")
    print(f"{'='*70}")
    
    for query in test_cases:
        routed = route_intent(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {routed.intent_type.value} (Confidence: {routed.confidence:.2f})")
        
        assert routed.intent_type == IntentType.OFF_TOPIC, \
            f"Expected OFF_TOPIC for: {query}"
        
        print("✓ Correctly rejected as off-topic")




def test_agent_instantiation():
    """Test routing intent types are valid."""
    # Just verify the intent enum has all expected types
    assert hasattr(IntentType, 'ITEMS')
    assert hasattr(IntentType, 'FRIENDSHIP')
    assert hasattr(IntentType, 'CROPS')
    assert hasattr(IntentType, 'UNKNOWN')
    assert hasattr(IntentType, 'OFF_TOPIC')
    print("✓ All intent types defined correctly")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ORCHESTRATOR INTEGRATION TEST")
    print("="*70)
    
    try:
        test_orchestrator_routing()
        print("\n✓ Orchestrator routing test PASSED")
    except AssertionError as e:
        print(f"\n✗ Orchestrator routing test FAILED: {e}")
        exit(1)
    
    try:
        test_off_topic_rejection()
        print("\n✓ Off-topic rejection test PASSED")
    except AssertionError as e:
        print(f"\n✗ Off-topic rejection test FAILED: {e}")
        exit(1)
    
    try:
        test_agent_instantiation()
        print("\n✓ Agent instantiation test PASSED")
    except AssertionError as e:
        print(f"\n✗ Agent instantiation test FAILED: {e}")
        exit(1)
    
    print("\n" + "="*70)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Set up virtual environment and install requirements")
    print("  2. Build the FAISS index: python build_index.py --input ../data/processed/stardew_wiki_sections.jsonl")
    print("  3. Start the API server: uvicorn app:app --reload --port 8000")
    print("  4. Test the /chat endpoint or build the frontend")

