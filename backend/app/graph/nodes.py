"""
LangGraph node functions for chatbot flow.
"""
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import logging
import json

from app.config import settings
from app.graph.state import ChatbotState

logger = logging.getLogger(__name__)


# Initialize Groq LLM
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.7
)


SYSTEM_PROMPT = """You are a friendly pizza delivery chatbot assistant. Your role is to:
1. Greet customers warmly
2. Help them browse the pizza menu
3. Answer questions about pizzas (ingredients, prices)
4. Add pizzas to their cart
5. Calculate the total price
6. Confirm their order

You have access to tools to check pizza prices and list available pizzas.
Be conversational, helpful, and guide customers through the ordering process.
When a customer asks about a pizza or wants to order, use the get_pizza_price tool.
"""


async def greeting_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Initial greeting node.
    Checks if this is the first message and provides a greeting.
    """
    messages = state.get("messages", [])

    # Only greet if this is the first interaction
    if len(messages) <= 1:
        greeting = "Hello! Welcome to our Pizza Delivery service! I'm here to help you order delicious pizzas. Would you like to see our menu or ask about a specific pizza?"

        messages.append({
            "role": "assistant",
            "content": greeting
        })

    return {"messages": messages}


async def llm_decision_node(state: ChatbotState, tools: list) -> Dict[str, Any]:
    """
    LLM processes the conversation and decides whether to use tools.

    Args:
        state: Current chatbot state
        tools: List of available LangChain tools

    Returns:
        Updated state with LLM response and potential tool call
    """
    messages = state.get("messages", [])

    # Convert messages to LangChain format
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Get LLM response
    response = await llm_with_tools.ainvoke(lc_messages)

    # Check if LLM wants to use a tool
    pending_tool_call = ""
    tool_result = ""

    if response.tool_calls:
        # LLM wants to use a tool
        tool_call = response.tool_calls[0]
        pending_tool_call = tool_call["name"]

        logger.info(f"LLM requested tool: {pending_tool_call}")
    else:
        # Regular response
        messages.append({
            "role": "assistant",
            "content": response.content
        })

    return {
        "messages": messages,
        "pending_tool_call": pending_tool_call,
        "tool_result": tool_result
    }


async def tool_execution_node(state: ChatbotState, tools: list) -> Dict[str, Any]:
    """
    Execute the tool requested by the LLM.

    Args:
        state: Current chatbot state
        tools: List of available tools

    Returns:
        Updated state with tool execution result
    """
    pending_tool_call = state.get("pending_tool_call", "")
    messages = state.get("messages", [])

    if not pending_tool_call:
        return state

    # Find and execute the tool
    tool_result = "Tool not found"

    for tool in tools:
        if tool.name == pending_tool_call:
            # Extract tool arguments from last user message
            user_message = messages[-1]["content"] if messages else ""

            try:
                # Execute tool
                result = await tool.ainvoke({"pizza_name": user_message})
                tool_result = result
                logger.info(f"Tool {pending_tool_call} executed successfully")
            except Exception as e:
                logger.error(f"Error executing tool {pending_tool_call}: {e}")
                tool_result = f"Error executing tool: {str(e)}"

            break

    # Add tool result to messages
    messages.append({
        "role": "assistant",
        "content": tool_result
    })

    return {
        "messages": messages,
        "tool_result": tool_result,
        "pending_tool_call": ""
    }


async def state_update_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Update cart state based on conversation.
    Extracts pizza additions from messages and updates cart.

    Args:
        state: Current chatbot state

    Returns:
        Updated state with cart items and total
    """
    # This is a simplified version - in production, you'd parse the conversation
    # more intelligently to extract orders

    cart_items = state.get("cart_items", [])
    total = state.get("total", 0.0)

    # TODO: Implement intelligent cart parsing from conversation
    # For now, we just maintain the existing cart

    return {
        "cart_items": cart_items,
        "total": total
    }


async def confirmation_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Final confirmation node.
    Summarizes the order and asks for confirmation.

    Args:
        state: Current chatbot state

    Returns:
        Updated state with confirmation message
    """
    cart_items = state.get("cart_items", [])
    total = state.get("total", 0.0)
    messages = state.get("messages", [])

    if cart_items:
        confirmation = f"Great! Your order summary:\n"
        for item in cart_items:
            confirmation += f"- {item['name']} (${item['price']:.2f})\n"
        confirmation += f"\nTotal: ${total:.2f}\n\nWould you like to proceed with this order?"

        messages.append({
            "role": "assistant",
            "content": confirmation
        })

    return {"messages": messages}
