"""
actions.py — Game-specific action handlers for multi-turn interactions.

Actions available:
1. CreateFriendshipPlan (multi-turn) — Collect villager + current hearts → create romance plan
2. CreateFarmPlan (multi-turn) — Collect plot count + budget → create crop plan
3. SaveFavorites (single-turn) — Save a villager's favorite gifts to session
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import difflib


class ActionType(Enum):
    """Available action types."""
    CREATE_FRIENDSHIP_PLAN = "create_friendship_plan"
    CREATE_FARM_PLAN = "create_farm_plan"
    SAVE_FAVORITES = "save_favorites"


@dataclass
class ActionContext:
    """Context for an in-progress action."""
    action_type: ActionType
    state: Dict[str, Any] = field(default_factory=dict)  # Collected parameters
    current_step: int = 0  # Multi-turn step counter
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_complete(self) -> bool:
        """Check if all required parameters collected."""
        if self.action_type == ActionType.CREATE_FRIENDSHIP_PLAN:
            return all(k in self.state for k in ["villager", "current_hearts", "gifts_per_week"])
        elif self.action_type == ActionType.CREATE_FARM_PLAN:
            return all(k in self.state for k in ["plot_count", "budget"])
        elif self.action_type == ActionType.SAVE_FAVORITES:
            return "villagers" in self.state and len(self.state.get("villagers", [])) > 0
        return False


@dataclass
class ActionResult:
    """Result of executing an action."""
    success: bool
    message: str
    action_id: Optional[str] = None  # For saved items
    metadata: Dict[str, Any] = field(default_factory=dict)


class ActionHandler:
    """Handles game-specific actions with state management."""
    
    VALID_VILLAGERS = [
        "Abigail", "Sebastian", "Haley", "Elliott", "Leah", 
        "Penny", "Emily", "Maru", "Alex", "Shane", "Harvey"
    ]
    
    def __init__(self):
        """Initialize action handler."""
        self.saved_plans: Dict[str, Dict[str, Any]] = {}  # Persisted across sessions
        self.plan_counter = 0
    
    def _find_villager_match(self, text: str) -> list[str]:
        """
        Find villager names in text with fuzzy matching.
        Returns list of valid villager names found (case-insensitive).
        """
        found_villagers = []
        text_lower = text.lower()
        text_words = text_lower.split()
        
        for villager in self.VALID_VILLAGERS:
            # Exact match (case-insensitive)
            if villager.lower() in text_lower:
                found_villagers.append(villager)
            else:
                # Fuzzy match for common misspellings (e.g., "Hayley" -> "Haley")
                matches = difflib.get_close_matches(villager.lower(), text_words, n=1, cutoff=0.75)
                if matches:
                    found_villagers.append(villager)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_villagers = []
        for v in found_villagers:
            if v not in seen:
                unique_villagers.append(v)
                seen.add(v)
        return unique_villagers
    
    # ── Action Detection ───────────────────────────────────────────────────────
    
    def detect_action_intent(self, user_message: str, context: Optional[ActionContext] = None) -> Optional[ActionContext]:
        """
        Detect if user is requesting an action.
        
        Returns: ActionContext if action detected, None otherwise
        """
        msg_lower = user_message.lower()
        action_type = None
        
        # Detect friendship plan request
        if any(phrase in msg_lower for phrase in [
            "friendship plan", "romance plan", "marry", "woo", "court",
            "plan to marry", "want to marry", "help me romance"
        ]):
            action_type = ActionType.CREATE_FRIENDSHIP_PLAN
        
        # Detect farm plan request
        elif any(phrase in msg_lower for phrase in [
            "farm plan", "crop plan", "plan my farm", "plan my crops",
            "optimize my farm", "farm layout"
        ]):
            action_type = ActionType.CREATE_FARM_PLAN
        
        # Detect save favorites request
        elif any(phrase in msg_lower for phrase in [
            "save", "bookmark", "remember", "store", "favorites", "favorite gift"
        ]):
            # Try to extract villager names (case-insensitive, fuzzy matching)
            villagers = self._find_villager_match(user_message)
            if villagers:
                action_type = ActionType.SAVE_FAVORITES
                ctx = ActionContext(action_type=action_type, state={}, current_step=0)
                ctx.state["villagers"] = villagers
                return ctx
        
        if action_type:
            return ActionContext(action_type=action_type, state={}, current_step=0)
        return None
    
    # ── Multi-turn Collection ──────────────────────────────────────────────────
    
    def get_next_question(self, action_context: ActionContext) -> str:
        """Get the next question to ask the user based on action progress with suggestions."""
        if action_context.action_type == ActionType.CREATE_FRIENDSHIP_PLAN:
            if "villager" not in action_context.state:
                return (
                    "**Which villager do you want to romance?**\n\n"
                    "Choose from: Abigail, Sebastian, Haley, Elliott, Leah, Penny, Emily, Maru, Alex, Shane, or Harvey"
                )
            elif "current_hearts" not in action_context.state:
                villager = action_context.state.get("villager", "them")
                return (
                    f"**What's your current friendship level with {villager}?** (Enter a number)\n\n"
                    "Range: 0-10 hearts\n"
                    "• 0 hearts = Just met\n"
                    "• 4 hearts = Like them\n"
                    "• 8 hearts = Love them\n"
                    "• 10 hearts = Max friendship (can marry!)"
                )
            elif "gifts_per_week" not in action_context.state:
                villager = action_context.state.get("villager", "them")
                return (
                    f"**How many gifts can you give {villager} per week?** (Enter a number)\n\n"
                    "Range: 0-7 gifts (one per day max)\n"
                    "• 1 gift/week = Casual\n"
                    "• 3 gifts/week = Committed\n"
                    "• 7 gifts/week = Maximum effort"
                )
        
        elif action_context.action_type == ActionType.CREATE_FARM_PLAN:
            if "plot_count" not in action_context.state:
                return (
                    "**How many crop plots do you have available?** (Enter a number)\n\n"
                    "Range: 1-100 plots\n"
                    "• Small farm: 5-10 plots\n"
                    "• Medium farm: 15-25 plots\n"
                    "• Large farm: 50+ plots"
                )
            elif "budget" not in action_context.state:
                plots = action_context.state.get("plot_count", 0)
                return (
                    f"**What's your budget for seeds for {plots} plots?** (Enter in gold)\n\n"
                    "Examples:\n"
                    "• 1,000g = Budget planting\n"
                    "• 5,000g = Standard investment\n"
                    "• 10,000g+ = Premium crops"
                )
        
        return "Ready to create your plan!"
    
    def collect_parameter(self, action_context: ActionContext, user_input: str) -> tuple[bool, str]:
        """
        Collect next parameter from user.
        
        Returns: (success, message) where success=True if parameter valid and collected
        """
        action = action_context.action_type
        
        if action == ActionType.CREATE_FRIENDSHIP_PLAN:
            # Collect villager
            if "villager" not in action_context.state:
                # Validate villager name
                valid_villagers = {
                    "abigail", "sebastian", "haley", "elliott", "leah",
                    "penny", "emily", "maru", "alex", "shane", "harvey"
                }
                villager_lower = user_input.strip().lower()
                if villager_lower in valid_villagers:
                    action_context.state["villager"] = user_input.strip()
                    return True, f"✅ Great! {user_input.strip()} it is!\n\nNext, tell me your current friendship level with them."
                else:
                    valid_list = "Abigail, Sebastian, Haley, Elliott, Leah, Penny, Emily, Maru, Alex, Shane, Harvey"
                    return False, f"❌ I don't recognize '{user_input}'.\n\n**Valid villagers:** {valid_list}\n\nPlease choose one from the list above."
            
            # Collect current hearts
            elif "current_hearts" not in action_context.state:
                try:
                    hearts = int(user_input.strip())
                    if 0 <= hearts <= 10:
                        action_context.state["current_hearts"] = hearts
                        villager = action_context.state.get("villager", "them")
                        return True, f"✅ {hearts} hearts with {villager}. Now, how many gifts per week can you manage?"
                    else:
                        return False, f"❌ Invalid heart level: {hearts}\n\n**Hearts must be 0-10** (you entered {hearts}).\n\nTry: 0, 2, 4, 6, 8, or 10"
                except ValueError:
                    return False, f"❌ '{user_input}' is not a number.\n\n**Please enter a number between 0-10**\n\nExample: 5"
            
            # Collect gifts per week
            elif "gifts_per_week" not in action_context.state:
                try:
                    gifts = int(user_input.strip())
                    if 0 <= gifts <= 7:
                        action_context.state["gifts_per_week"] = gifts
                        return True, f"✅ Perfect! {gifts} gifts per week. All set — creating your plan now!"
                    else:
                        return False, f"❌ Invalid gift frequency: {gifts}\n\n**Can't give more than 7 gifts per week** (max 1 per day).\n\nTry: 1, 3, 5, or 7"
                except ValueError:
                    return False, f"❌ '{user_input}' is not a number.\n\n**Please enter a number between 0-7**\n\nExample: 3"
        
        elif action == ActionType.CREATE_FARM_PLAN:
            # Collect plot count
            if "plot_count" not in action_context.state:
                try:
                    plots = int(user_input.strip())
                    if 0 < plots <= 100:
                        action_context.state["plot_count"] = plots
                        return True, f"✅ {plots} plots noted. Now, what's your seed budget?"
                    else:
                        return False, f"❌ Invalid plot count: {plots}\n\n**Plots must be 1-100**.\n\nTry: 10, 20, 50, etc."
                except ValueError:
                    return False, f"❌ '{user_input}' is not a number.\n\n**Please enter a number between 1-100**\n\nExample: 25"
            
            # Collect budget
            elif "budget" not in action_context.state:
                try:
                    budget = int(user_input.strip())
                    if budget > 0:
                        action_context.state["budget"] = budget
                        return True, f"✅ {budget}g budget set. Creating your farm plan now!"
                    else:
                        return False, f"❌ Invalid budget: {budget}\n\n**Budget must be positive (>0)**.\n\nTry: 1000, 5000, 10000"
                except ValueError:
                    return False, f"❌ '{user_input}' is not a number.\n\n**Please enter your budget in gold**\n\nExample: 5000"
        
        return False, "Parameter collection error. Please try again."
    
    # ── Action Execution ──────────────────────────────────────────────────────
    
    def execute_action(self, action_context: ActionContext) -> ActionResult:
        """Execute the action and return result."""
        if not action_context.is_complete():
            return ActionResult(
                success=False,
                message="Action incomplete - missing required parameters."
            )
        
        if action_context.action_type == ActionType.CREATE_FRIENDSHIP_PLAN:
            return self._create_friendship_plan(action_context)
        elif action_context.action_type == ActionType.CREATE_FARM_PLAN:
            return self._create_farm_plan(action_context)
        elif action_context.action_type == ActionType.SAVE_FAVORITES:
            return self._save_favorites(action_context)
        
        return ActionResult(success=False, message="Unknown action type.")
    
    def _create_friendship_plan(self, ctx: ActionContext) -> ActionResult:
        """Generate a personalized friendship/romance plan."""
        villager = ctx.state["villager"]
        current = ctx.state["current_hearts"]
        gifts_per_week = ctx.state["gifts_per_week"]
        
        # Mock calculation: (10 - current) / (gifts_per_week * 2) weeks to 10 hearts, then 10+ more to marriage
        weeks_to_ten = max(1, (10 - current) // (gifts_per_week or 1) + 1)
        weeks_to_marriage = weeks_to_ten + (10 // (gifts_per_week or 1) + 2)
        
        plan = {
            "villager": villager,
            "start_hearts": current,
            "weeks_to_10_hearts": weeks_to_ten,
            "weeks_to_marriage": weeks_to_marriage,
            "gifts_per_week": gifts_per_week,
            "tip": f"Gift {villager} consistently each week and attend their events for faster friendship gains!"
        }
        
        plan_id = f"friendship_plan_{self.plan_counter}"
        self.plan_counter += 1
        self.saved_plans[plan_id] = plan
        
        # Detailed message with plan breakdown
        detailed_message = f"""✅ **Romance Plan Created for {villager}!**

📊 **Current Status:** {current}/10 hearts

📅 **Timeline to Romance:**
• Current → 10 Hearts: **~{weeks_to_ten} weeks** with {gifts_per_week} gift(s) per week
• 10 Hearts → Marriage: **~{weeks_to_marriage - weeks_to_ten} additional weeks**
• **Total to Marriage: ~{weeks_to_marriage} weeks**

💝 **Gifting Strategy:**
• Gift frequency: {gifts_per_week} gift(s) per week
• Best days: {villager}'s birthday (double hearts!) + 2 random days
• Tip: {plan['tip']}

🎯 **Pro Tips:**
• Talk to {villager} every day (+20 friendship points)
• Attend events they like and watch them
• Return lost items for +150 friendship
• Never give gifts they dislike!"""
        
        return ActionResult(
            success=True,
            message=detailed_message,
            action_id=plan_id,
            metadata=plan
        )
    
    def _create_farm_plan(self, ctx: ActionContext) -> ActionResult:
        """Generate a profitable crop plan."""
        plots = ctx.state["plot_count"]
        budget = ctx.state["budget"]
        
        # Mock crop recommendations (would use real data in production)
        recommended_crops = [
            {"name": "Parsnip", "profit_per_day": 5, "growth_time": 4},
            {"name": "Cauliflower", "profit_per_day": 12, "growth_time": 12},
            {"name": "Potato", "profit_per_day": 8, "growth_time": 6},
        ]
        
        affordable = [c for c in recommended_crops if c["profit_per_day"] * budget / plots >= 10]
        
        plan = {
            "plots": plots,
            "budget": budget,
            "recommended_crops": affordable if affordable else recommended_crops[:2],
            "roi_estimate": f"{budget * 2}-{budget * 3} gold in first season"
        }
        
        plan_id = f"farm_plan_{self.plan_counter}"
        self.plan_counter += 1
        self.saved_plans[plan_id] = plan
        
        # Detailed farm plan message
        crops_list = "\n".join([f"• **{c['name']}**: {c['profit_per_day']} gold/day, grows in {c['growth_time']} days" 
                                for c in plan['recommended_crops']])
        
        detailed_message = f"""✅ **Farm Plan Created!**

🌾 **Farm Setup:**
• Total Plots: {plots}
• Budget: {budget}g
• Estimated ROI: {plan['roi_estimate']}

🌱 **Recommended Crops:**
{crops_list}

💡 **Pro Tips:**
• Plant in spring for best prices
• Water daily for faster growth
• Use fertilizer for quality (+10% profit)
• Rotate crops to prevent boredom
• Sell at the Shipping Bin before midnight"""
        
        return ActionResult(
            success=True,
            message=detailed_message,
            action_id=plan_id,
            metadata=plan
        )
    
    def _save_favorites(self, ctx: ActionContext) -> ActionResult:
        """Save a villager's favorite gifts."""
        villagers = ctx.state.get("villagers", [])
        if not villagers:
            return ActionResult(
                success=False,
                message="No villagers specified for saving favorites."
            )
        
        # Mock favorite gifts data
        favorites = {
        "abigail":  ["Amethyst", "Chocolate Cake", "Pumpkin"],
        "sebastian": ["Frozen Tear", "Obsidian", "Void Egg"], 
        "haley":    ["Coconut", "Fruit Salad", "Pink Cake"],
        "emily":    ["Amethyst", "Aquamarine", "Cloth"],
        "penny":    ["Emerald", "Melon", "Poppy"],
        "leah":     ["Goat Cheese", "Salad", "Wine"],
        "maru":     ["Battery Pack", "Cauliflower", "Diamond"],
        "harvey":   ["Coffee", "Pickles", "Truffle Oil"],
        "elliott":  ["Crab Cakes", "Duck Feather", "Pomegranate"],
        "shane":    ["Hot Pepper", "Beer", "Pizza"],
        "alex":     ["Complete Breakfast", "Salmon Dinner"],
    }
            
        # Build summary for all villagers
        save_id = f"favorites_{len(villagers)}_villagers_{int(datetime.now().timestamp())}"
        saved_data = {}
        summary_lines = []
        
        for villager in villagers:
            gifts = favorites.get(villager.lower(), ["Ruby", "Gold Bar"])
            saved_data[villager] = gifts
            summary_lines.append(f"\n💝 **{villager}:**\n" + "\n".join([f"• {gift}" for gift in gifts]))
        
        self.saved_plans[save_id] = saved_data
        
        gifts_summary = "".join(summary_lines)
        
        detailed_message = f"""✅ **Saved Favorite Gifts for {", ".join(villagers)}!**

{gifts_summary}

📝 **Tips:**
• Give these gifts to earn +80 friendship points each
• Give on their birthday for double points (+160!)
• Avoid giving disliked items (which lose -20 points)
• Keep this list handy when shopping at Pierre's or Joja Mart

🎯 **Quick Strategy:**
• Aim for 3 gifts per week of favorites per villager
• Mix in a birthday gift for faster friendship gains
• Combine with daily conversations for best results"""
        
        return ActionResult(
            success=True,
            message=detailed_message,
            action_id=save_id,
            metadata={"villagers": villagers, "gifts": saved_data}
        )
    
    def retrieve_saved(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a previously saved plan."""
        return self.saved_plans.get(plan_id)
    
    def list_saved(self) -> Dict[str, Dict[str, Any]]:
        """List all saved plans in current session."""
        return self.saved_plans


# Global action handler (shared across requests in a session)
_handler: Optional[ActionHandler] = None


def get_action_handler() -> ActionHandler:
    """Get or create the global action handler."""
    global _handler
    if _handler is None:
        _handler = ActionHandler()
    return _handler
