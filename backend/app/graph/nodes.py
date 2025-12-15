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
# Temperature 0.1 for maximum deterministic tool calling
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.1,  # Very low for reliable tool calling
    timeout=30  # Prevent hanging requests
)


SYSTEM_PROMPT = """Você é um assistente virtual de delivery de pizza chamado Pizza Bot.

IMPORTANTE: Você NÃO tem informações sobre pizzas ou preços em seu conhecimento.
TODA informação sobre pizzas DEVE vir das ferramentas disponíveis.

FERRAMENTAS DISPONÍVEIS:

1. list_all_pizzas() - Use quando:
   - Cliente pede "cardápio", "menu", "quais pizzas", "mostre as pizzas"
   - Retorna: Lista completa de pizzas com preços

2. get_pizza_price(pizza_name) - Use quando:
   - Cliente pergunta preço: "quanto custa [pizza]", "preço de [pizza]"
   - Cliente quer saber mais: "fale sobre [pizza]", "ingredientes de [pizza]"
   - Retorna: Preço e ingredientes da pizza

3. add_to_cart(pizza_name, quantity) - Use quando:
   - Cliente quer adicionar: "quero", "vou levar", "adiciona", "coloca"
   - Retorna: Confirmação da adição ao carrinho

COMPORTAMENTO ESPERADO (SIGA EXATAMENTE ESTES EXEMPLOS):

SAUDAÇÕES (NÃO use ferramentas):
- Cliente diz: "oi", "olá", "boa noite"
- Você responde: "Olá! Bem-vindo à Pizza Bot. Gostaria de ver o cardápio ou fazer um pedido?"
- NÃO chame list_all_pizzas() automaticamente

MOSTRAR CARDÁPIO (use list_all_pizzas):
- Cliente diz: "quero ver o cardápio", "mostre o menu", "quais pizzas tem"
- Você chama: list_all_pizzas()
- Você responde: "Aqui estão nossas pizzas disponíveis:
  - Margherita: R$ 35,90
  - Calabresa: R$ 39,90
  - Quatro Queijos: R$ 45,90
  - Portuguesa: R$ 42,90
  - Frango com Catupiry: R$ 43,90
  - Bacon: R$ 41,90
  - Vegetariana: R$ 40,90
  - Napolitana: R$ 38,90
  - Lombo Canadense: R$ 44,90
  - Especial da Casa: R$ 47,90

  Qual pizza você gostaria de pedir?"
- IMPORTANTE: Mostre TODAS as 10 pizzas retornadas pela ferramenta

CONSULTA DE PREÇO/DETALHES (use get_pizza_price):
- Cliente diz: "quanto custa a Calabresa?", "fale mais sobre a Vegetariana"
- Você chama: get_pizza_price("Calabresa") ou get_pizza_price("Vegetariana")
- Você responde: "A pizza de [nome] custa R$ [preço] e leva [COPIE os ingredientes retornados]. Gostaria de adicionar ao carrinho?"

ADICIONAR AO CARRINHO (use add_to_cart):
- Cliente diz: "vou querer uma", "quero 2 calabresas"
- Contexto: Cliente acabou de perguntar sobre uma pizza específica
- Você chama: add_to_cart("[nome da pizza do contexto]", [quantidade])
- Você responde: "Perfeito! Adicionei [quantidade]x [pizza] ao seu carrinho. O total é R$ [total]. Deseja mais alguma coisa?"

FINALIZAR (NÃO use ferramentas):
- Cliente diz: "não, pode fechar", "já deu", "é só isso", "consegue fechar assim", "pode finalizar"
- Você responde: "Pedido confirmado! [resumo do carrinho]. Obrigado pela preferência!"
- IMPORTANTE: NÃO chame add_to_cart ou qualquer outra ferramenta ao finalizar
- Os itens já estão no carrinho, apenas confirme o pedido

REGRAS CRÍTICAS:

1. SEMPRE use ferramentas para obter dados sobre pizzas (preços, cardápio, ingredientes)
2. NUNCA invente preços, nomes de pizzas ou ingredientes
3. **CRÍTICO**: SEMPRE inclua o resultado COMPLETO das ferramentas na sua resposta ao usuário
   - Quando usar list_all_pizzas(), COPIE e MOSTRE a lista completa de pizzas na sua resposta
   - Quando usar get_pizza_price(), COPIE e MOSTRE os ingredientes na sua resposta
   - NUNCA responda sem incluir o resultado da ferramenta que você acabou de chamar
4. Quando chamar list_all_pizzas(), mostre TODAS as 10 pizzas retornadas, não apenas pergunte
5. Quando chamar get_pizza_price(), copie TODOS os ingredientes retornados, não apenas o preço
6. NUNCA chame ferramentas ao finalizar o pedido
7. Seja natural, educado e responda em português do Brasil
8. Use as ferramentas no formato JSON correto (nunca use XML ou outros formatos)
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

    # Bind tools to LLM using bind_tools (proper method for Groq)
    logger.info(f"Binding {len(tools)} tools to LLM")
    llm_with_tools = llm.bind_tools(tools)

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
        "tool_result": tool_result,
        "step_count": state.get("step_count", 0) + 1  # Increment step counter
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

    # Execute ALL tool calls (support for parallel tool calling)
    last_tool_result = ""
    for tool_call in tool_calls_data:
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

        # Add ToolMessage to conversation for each tool call
        messages.append({
            "role": "tool",
            "content": tool_result,
            "tool_call_id": tool_call_id,
            "name": tool_name
        })
        last_tool_result = tool_result

    return {
        "messages": messages,
        "tool_result": last_tool_result,
        "pending_tool_call": "",
        "step_count": state.get("step_count", 0)  # Pass through step counter
    }


async def state_update_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Update cart state based on add_to_cart tool results.

    Parses the conversation messages looking for tool results from add_to_cart,
    extracts the pizza information (name, price, quantity), and updates the
    shopping cart accordingly.

    Args:
        state: Current chatbot state

    Returns:
        Updated state with cart items and total
    """
    messages = state.get("messages", [])
    cart_items = state.get("cart_items", [])
    total = state.get("total", 0.0)

    # Track which tool messages we've already processed to avoid duplicates
    # We'll use a state variable or just process new unprocessed messages
    processed_count = state.get("processed_tool_count", 0)

    # Count how many tool messages exist
    tool_messages = [msg for msg in messages if msg.get("role") == "tool" and msg.get("name") == "add_to_cart"]
    new_tool_messages = tool_messages[processed_count:]

    # Process all NEW tool results from add_to_cart
    for msg in new_tool_messages:
        try:
            # Parse the JSON result from add_to_cart tool
            tool_result = json.loads(msg["content"])

            if tool_result.get("action") == "add_to_cart":
                pizza_name = tool_result["pizza_name"]
                price = tool_result["price"]
                quantity = tool_result["quantity"]

                # Check if this pizza is already in the cart
                existing_item = next(
                    (item for item in cart_items if item["name"] == pizza_name),
                    None
                )

                if existing_item:
                    # Update quantity of existing item
                    existing_item["quantity"] += quantity
                    logger.info(f"Updated quantity for {pizza_name}: {existing_item['quantity']}")
                else:
                    # Add new item to cart
                    cart_items.append({
                        "name": pizza_name,
                        "price": price,
                        "quantity": quantity
                    })
                    logger.info(f"Added new item to cart: {quantity}x {pizza_name} @ R$ {price:.2f}")

        except json.JSONDecodeError:
            logger.warning(f"Could not parse add_to_cart result: {msg['content']}")
            continue
        except KeyError as e:
            logger.error(f"Missing key in add_to_cart result: {e}")
            continue

    # Recalculate total after processing all items
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    if new_tool_messages:
        logger.info(f"Cart updated. Total items: {len(cart_items)}, Total: R$ {total:.2f}")

    return {
        "messages": messages,
        "cart_items": cart_items,
        "total": total,
        "processed_tool_count": len(tool_messages)
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
