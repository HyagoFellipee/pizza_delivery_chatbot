"""
LangGraph state definition for chatbot.
"""
from typing import TypedDict, List, Dict, Any


class ChatbotState(TypedDict):
    """
    State schema for the pizza delivery chatbot.

    Attributes:
        messages: List of conversation messages (role + content)
        cart_items: List of items in the shopping cart
        total: Total price of items in cart
        pending_tool_call: Name of tool waiting to be executed
        tool_result: Result from the last tool execution
        processed_tool_count: Number of tool messages already processed
        step_count: Number of LLM invocations (prevents infinite loops)
    """
    messages: List[Dict[str, str]]
    cart_items: List[Dict[str, Any]]
    total: float
    pending_tool_call: str
    tool_result: str
    processed_tool_count: int
    step_count: int
