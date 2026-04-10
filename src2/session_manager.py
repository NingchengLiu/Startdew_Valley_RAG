"""
session_manager.py — Session and conversation memory management.

Tracks per-user:
- Chat history (messages, timestamps, intent)
- Action state (in-progress actions, collected parameters)
- Saved items (plans, favorites)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from actions import ActionContext, ActionType


@dataclass
class Message:
    """Single message in conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent_type: Optional[str] = None  # e.g., "FRIENDSHIP", "ITEMS"
    action_type: Optional[str] = None  # e.g., "CREATE_FRIENDSHIP_PLAN"


@dataclass
class SessionState:
    """Session state for a user."""
    session_id: str
    user_id: str
    messages: List[Message] = field(default_factory=list)
    action_context: Optional[ActionContext] = None
    saved_items: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, intent_type: Optional[str] = None, action_type: Optional[str] = None):
        """Add a message to the conversation history."""
        self.messages.append(Message(
            role=role,
            content=content,
            intent_type=intent_type,
            action_type=action_type
        ))
        self.last_activity = datetime.now()
    
    def get_context_window(self, max_messages: int = 5) -> str:
        """Get recent conversation context for reference."""
        recent = self.messages[-max_messages:]
        context = "\n".join([
            f"[{m.role.upper()}] {m.content}"
            for m in recent
        ])
        return context if context else "No previous context."
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session state."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "has_action_in_progress": self.action_context is not None,
            "action_type": self.action_context.action_type.value if self.action_context else None,
            "saved_items": list(self.saved_items.keys()),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }


class SessionManager:
    """Manages user sessions and conversation memory."""
    
    def __init__(self, max_sessions: int = 100, timeout_minutes: int = 30):
        """
        Initialize session manager.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            timeout_minutes: Session timeout in minutes
        """
        self.sessions: Dict[str, SessionState] = {}
        self.max_sessions = max_sessions
        self.timeout_minutes = timeout_minutes
    
    # ── Session Management ─────────────────────────────────────────────────────
    
    def create_session(self, user_id: str, session_id: str) -> SessionState:
        """Create a new session for a user."""
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest inactive session
            oldest = min(self.sessions.values(), key=lambda s: s.last_activity)
            del self.sessions[oldest.session_id]
        
        session = SessionState(session_id=session_id, user_id=user_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve an existing session."""
        return self.sessions.get(session_id)
    
    def end_session(self, session_id: str) -> bool:
        """End a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user."""
        return [
            sid for sid, session in self.sessions.items()
            if session.user_id == user_id
        ]
    
    # ── Conversation History ───────────────────────────────────────────────────
    
    def add_user_message(
        self,
        session_id: str,
        content: str,
        intent_type: Optional[str] = None,
        action_type: Optional[str] = None
    ) -> bool:
        """Add a user message to session history."""
        session = self.get_session(session_id)
        if session:
            session.add_message("user", content, intent_type, action_type)
            return True
        return False
    
    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        intent_type: Optional[str] = None,
        action_type: Optional[str] = None
    ) -> bool:
        """Add an assistant message to session history."""
        session = self.get_session(session_id)
        if session:
            session.add_message("assistant", content, intent_type, action_type)
            return True
        return False
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages[-limit:]
        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "intent": m.intent_type,
                "action": m.action_type
            }
            for m in messages
        ]
    
    def get_context(self, session_id: str) -> str:
        """Get recent context window for a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_context_window()
        return ""
    
    # ── Action State Management ────────────────────────────────────────────────
    
    def set_action_context(self, session_id: str, action_context: ActionContext) -> bool:
        """Set the current action being performed."""
        session = self.get_session(session_id)
        if session:
            session.action_context = action_context
            return True
        return False
    
    def get_action_context(self, session_id: str) -> Optional[ActionContext]:
        """Get the current action context."""
        session = self.get_session(session_id)
        if session:
            return session.action_context
        return None
    
    def clear_action_context(self, session_id: str) -> bool:
        """Clear the current action context."""
        session = self.get_session(session_id)
        if session:
            session.action_context = None
            return True
        return False
    
    # ── Saved Items ────────────────────────────────────────────────────────────
    
    def save_item(self, session_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Save an item (plan, favorite, etc) to session."""
        session = self.get_session(session_id)
        if session:
            session.saved_items[item_id] = item_data
            return True
        return False
    
    def get_saved_item(self, session_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a saved item."""
        session = self.get_session(session_id)
        if session:
            return session.saved_items.get(item_id)
        return None
    
    def list_saved_items(self, session_id: str) -> Dict[str, Any]:
        """List all saved items in a session."""
        session = self.get_session(session_id)
        if session:
            return session.saved_items
        return {}
    
    # ── Session Info ───────────────────────────────────────────────────────────
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_session_summary()
        return None


# Global session manager (shared across requests)
_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
