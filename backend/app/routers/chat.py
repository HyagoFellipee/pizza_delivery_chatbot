"""
Chat API endpoint for interacting with the LangGraph chatbot.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.connection import get_session
from app.graph.chatbot_graph import create_chatbot_graph

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Chat request payload"""
    message: str
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    """Chat response payload"""
    response: str
    cart_items: List[Dict[str, Any]] = []
    total: float = 0.0


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session)
) -> ChatResponse:
    """
    Process chat message through LangGraph chatbot.

    Args:
        request: Chat request with user message and conversation history
        session: Database session

    Returns:
        ChatResponse with bot response, cart items, and total
    """
    try:
        # Create chatbot graph
        graph = create_chatbot_graph(session)

        # Prepare initial state
        initial_state = {
            "messages": [msg.dict() for msg in request.conversation_history],
            "cart_items": [],
            "total": 0.0
        }

        # Add user message
        initial_state["messages"].append({
            "role": "user",
            "content": request.message
        })

        # Run the graph
        final_state = await graph.ainvoke(initial_state)

        # Extract response
        assistant_messages = [
            msg for msg in final_state.get("messages", [])
            if msg.get("role") == "assistant"
        ]

        response_content = assistant_messages[-1]["content"] if assistant_messages else "I'm sorry, I couldn't process that request."

        return ChatResponse(
            response=response_content,
            cart_items=final_state.get("cart_items", []),
            total=final_state.get("total", 0.0)
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )
