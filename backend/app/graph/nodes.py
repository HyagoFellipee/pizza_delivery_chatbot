"""
LangGraph node functions for chatbot flow.
"""
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
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


SYSTEM_PROMPT = """Você é um assistente virtual amigável de delivery de pizza. Seu papel é:
1. Cumprimentar os clientes calorosamente
2. Ajudá-los a navegar pelo cardápio de pizzas
3. Responder perguntas sobre pizzas (ingredientes, preços)
4. Adicionar pizzas ao carrinho
5. Calcular o preço total
6. Confirmar o pedido

Você tem acesso a ferramentas para consultar preços de pizzas e listar pizzas disponíveis.
Seja conversacional, prestativo e guie os clientes pelo processo de pedido.
Quando um cliente perguntar sobre uma pizza ou quiser pedir, use a ferramenta get_pizza_price.
Sempre responda em português brasileiro.
"""


async def greeting_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Initial greeting node.
    Checks if this is the first message and provides a greeting.
    """
    messages = state.get("messages", [])

    # Only greet if this is truly the first interaction (no messages OR only has one user message with no assistant responses)
    has_assistant_message = any(msg.get("role") == "assistant" for msg in messages)

    if not has_assistant_message and len(messages) == 1:
        greeting = "Olá! Bem-vindo ao nosso serviço de delivery de pizza! Estou aqui para ajudá-lo a pedir pizzas deliciosas. Gostaria de ver nosso cardápio ou perguntar sobre uma pizza específica?"

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
            tool_calls_data = msg.get("tool_calls")
            if tool_calls_data:
                # AIMessage with tool calls
                lc_messages.append(AIMessage(
                    content=msg.get("content", ""),
                    tool_calls=tool_calls_data
                ))
            else:
                # Regular AIMessage
                lc_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "tool":
            # Tool result message
            lc_messages.append(ToolMessage(
                content=msg["content"],
                tool_call_id=msg["tool_call_id"],
                name=msg.get("name", "")
            ))

    # Log messages being sent
    logger.info(f"Sending {len(lc_messages)} messages to LLM")
    for i, msg in enumerate(lc_messages):
        logger.info(f"Message {i}: {type(msg).__name__} - {msg.content[:100]}")

    # Convert tools to format that Groq expects
    from langchain_core.utils.function_calling import convert_to_openai_tool

    tool_definitions = [convert_to_openai_tool(tool) for tool in tools]
    logger.info(f"Tool definitions: {len(tool_definitions)} tools")

    # Bind tools to LLM
    llm_with_tools = llm.bind(tools=tool_definitions)

    # Get LLM response
    response = await llm_with_tools.ainvoke(lc_messages)

    logger.info(f"LLM response type: {type(response)}, content: '{response.content}'")

    # Check if LLM wants to use a tool
    pending_tool_call = ""
    tool_result = ""

    # Check for tool calls - use getattr for compatibility
    tool_calls = getattr(response, 'tool_calls', None) or []
    logger.info(f"Tool calls detected: {tool_calls}")

    if tool_calls:
        # LLM wants to use a tool - preserve tool_calls information
        logger.info(f"LLM requested tool: {tool_calls[0]['name']}")

        messages.append({
            "role": "assistant",
            "content": response.content or "",  # Handle None content
            "tool_calls": [{
                "name": tc["name"],
                "args": tc.get("args", {}),
                "id": tc.get("id", "")
            } for tc in tool_calls]
        })
        pending_tool_call = tool_calls[0]["name"]
    else:
        # Regular response
        logger.info(f"Adding regular response to messages: '{response.content}'")
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
    messages = state.get("messages", [])

    # Get tool call information from last assistant message
    last_message = messages[-1] if messages else {}
    tool_calls_data = last_message.get("tool_calls", [])

    if not tool_calls_data:
        return state

    tool_call = tool_calls_data[0]
    tool_name = tool_call["name"]
    tool_args = tool_call.get("args", {})
    tool_call_id = tool_call.get("id", "")

    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

    # Find and execute the tool
    tool_result = "Tool not found"

    for tool in tools:
        if tool.name == tool_name:
            try:
                # Execute tool with proper arguments
                result = await tool.ainvoke(tool_args)
                tool_result = result
                logger.info(f"Tool {tool_name} executed successfully: {tool_result}")
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_result = f"Erro ao executar ferramenta: {str(e)}"
            break

    # Add ToolMessage to conversation
    messages.append({
        "role": "tool",
        "content": tool_result,
        "tool_call_id": tool_call_id,
        "name": tool_name
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
        confirmation = f"Ótimo! Resumo do seu pedido:\n"
        for item in cart_items:
            confirmation += f"- {item['name']} (R$ {item['price']:.2f})\n"
        confirmation += f"\nTotal: R$ {total:.2f}\n\nGostaria de finalizar este pedido?"

        messages.append({
            "role": "assistant",
            "content": confirmation
        })

    return {"messages": messages}
