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
    cart_items: List[Dict[str, Any]] = []
    total: float = 0.0


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

        # Prepare initial state with cart from request
        # Filter out any tool-related messages from frontend (they shouldn't be sent, but filter just in case)
        clean_history = []
        for msg in request.conversation_history:
            msg_dict = msg.dict()
            # Only keep user and assistant messages, remove tool_calls from assistant messages
            if msg_dict.get("role") in ["user", "assistant"]:
                # Remove tool_calls if present (assistant messages from previous interactions)
                if "tool_calls" in msg_dict:
                    del msg_dict["tool_calls"]
                clean_history.append(msg_dict)

        initial_state = {
            "messages": clean_history,
            "cart_items": request.cart_items,
            "total": request.total,
            "processed_tool_count": 0
        }

        # Add user message
        initial_state["messages"].append({
            "role": "user",
            "content": request.message
        })

        # Run the graph
        final_state = await graph.ainvoke(initial_state)

        logger.info(f"Final state messages: {final_state.get('messages', [])}")

        # Extract response - get ONLY the last assistant message
        # The LLM already incorporates tool results into its response
        messages = final_state.get("messages", [])

        response_content = "Desculpe, não consegui processar sua mensagem."

        # Find last assistant message with content
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                response_content = msg["content"]
                break

        logger.info(f"Response content: {response_content}")

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
