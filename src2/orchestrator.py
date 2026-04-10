"""
orchestrator.py — LLM-based intent routing for multi-agent Stardew Valley chatbot.

This orchestrator uses an LLM to classify user queries into intent types:
  - ItemFinder: Find items, resources, locations, materials
  - FriendshipFinder: Village friendships, romance, dialogue, heart events
  - CropPlanner: Crops, seasons, farming, growth, profit
  - DefaultAgent: General Stardew Valley questions
  - OffTopic: Non-Stardew questions (rejection)
"""

from enum import Enum
from typing import Optional
from llm import LLMClient, get_llm_client
import json


class IntentType(Enum):
    """Classification of user intent."""
    ITEMS = "items"              # item_finder agent
    FRIENDSHIP = "friendship"    # friendship_finder agent
    CROPS = "crops"              # crop_planner agent
    UNKNOWN = "unknown"          # default fallback
    OFF_TOPIC = "off_topic"      # not about Stardew


class RoutedIntent:
    """Result of intent routing."""
    def __init__(
        self,
        intent_type: IntentType,
        confidence: float,
        probabilities: dict,
        original_query: str,
    ):
        self.intent_type = intent_type
        self.confidence = confidence
        self.probabilities = probabilities  # All intent probabilities
        self.original_query = original_query


class IntentRouter:
    """
    LLM-based intent classifier.
    
    Uses an LLM to classify user queries and provide confidence scores
    for each intent type. More accurate than keyword matching.
    """
    
    ROUTING_PROMPT = """\
You are an expert at classifying Stardew Valley player questions into intent categories.

Available intent categories:
1. ITEMS - Questions about items, tools, resources, crafting, where to find things
2. FRIENDSHIP - Questions about villagers, romance, gifts, marriage, heart events  
3. CROPS - Questions about farming, crops, seasons, planting, growth, profit
4. UNKNOWN - General Stardew Valley questions that don't fit above categories
5. OFF_TOPIC - Questions NOT about Stardew Valley at all

Respond with ONLY a JSON object with this structure:
{
    "intent": "ITEMS|FRIENDSHIP|CROPS|UNKNOWN|OFF_TOPIC",
    "confidence": 0.0-1.0,
    "probabilities": {
        "items": 0.0-1.0,
        "friendship": 0.0-1.0,
        "crops": 0.0-1.0,
        "unknown": 0.0-1.0,
        "off_topic": 0.0-1.0
    }
}

The probabilities should sum to ~1.0 and represent the likelihood of each intent.
The intent field should be the most likely category.
Confidence should reflect how certain you are about the classification.

Examples:
- "How do I craft a chest?" → ITEMS (high confidence)
- "How do I marry Abigail?" → FRIENDSHIP (high confidence)
- "What should I plant in spring?" → CROPS (high confidence)
- "What's the weather today?" → OFF_TOPIC (high confidence)
- "Tell me about Stardew" → UNKNOWN (moderate confidence)
"""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or get_llm_client()
    
    def route(self, query: str) -> RoutedIntent:
        """
        Route a query to an intent type using LLM classification.
        
        Returns:
            RoutedIntent with intent_type, confidence, and probabilities
        """
        # Call LLM to classify
        try:
            response = self.llm.complete(
                messages=[
                    {
                        "role": "user",
                        "content": f"Classify this Stardew Valley question:\n\n{query}"
                    }
                ],
                system=self.ROUTING_PROMPT,
                max_tokens=200,
                temperature=0.3,  # Low temp for consistent classification
            )
            
            # Parse JSON response
            response_text = response.answer.strip()
            # Try to extract JSON if it's wrapped in code blocks
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            
            # Map string intent to enum
            intent_map = {
                "ITEMS": IntentType.ITEMS,
                "FRIENDSHIP": IntentType.FRIENDSHIP,
                "CROPS": IntentType.CROPS,
                "UNKNOWN": IntentType.UNKNOWN,
                "OFF_TOPIC": IntentType.OFF_TOPIC,
            }
            
            intent_type = intent_map.get(result["intent"], IntentType.UNKNOWN)
            confidence = float(result.get("confidence", 0.5))
            probabilities = result.get("probabilities", {})
            
            return RoutedIntent(
                intent_type=intent_type,
                confidence=confidence,
                probabilities=probabilities,
                original_query=query,
            )
        
        except Exception as e:
            # Fallback: return UNKNOWN if LLM fails
            print(f"[orchestrator] LLM routing failed, using fallback: {e}")
            return RoutedIntent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.3,
                probabilities={},
                original_query=query,
            )


def route_intent(query: str, llm: Optional[LLMClient] = None) -> RoutedIntent:
    """
    Convenience function: route a query to an intent type using LLM.
    
    Usage:
        intent = route_intent("How do I increase friendship with Abigail?")
        print(intent.intent_type)  # IntentType.FRIENDSHIP
        print(intent.confidence)   # 0.85
    """
    router = IntentRouter(llm=llm)
    return router.route(query)
