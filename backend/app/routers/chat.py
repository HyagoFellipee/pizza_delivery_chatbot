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
        initial_state = {
            "messages": [msg.dict() for msg in request.conversation_history],
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

        # Extract response - combine tool results and final assistant message
        messages = final_state.get("messages", [])
        response_parts = []

        # Get messages after the last user message
        for i, msg in enumerate(messages):
            if msg.get("role") == "user" and msg["content"] == request.message:
                # Found the user message, get everything after it
                subsequent_messages = messages[i+1:]
                for subsequent in subsequent_messages:
                    if subsequent.get("role") == "tool":
                        # Skip add_to_cart tool results (they're JSON for state_update_node)
                        # Include other tool results (like pizza prices, lists)
                        tool_name = subsequent.get("name", "")
                        if tool_name != "add_to_cart":
                            response_parts.append(subsequent["content"])
                    elif subsequent.get("role") == "assistant" and subsequent.get("content"):
                        # Include final assistant response
                        response_parts.append(subsequent["content"])
                break

        response_content = "\n\n".join(response_parts) if response_parts else "Desculpe, não consegui processar sua mensagem."

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
