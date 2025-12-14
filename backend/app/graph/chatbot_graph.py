"""
LangGraph StateGraph definition for pizza delivery chatbot.
"""
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.graph.state import ChatbotState
from app.graph.nodes import (
    greeting_node,
    llm_decision_node,
    tool_execution_node,
    state_update_node
)
from app.tools.pizza_tools import create_pizza_tools

logger = logging.getLogger(__name__)


def create_chatbot_graph(session: AsyncSession):
    """
    Create the LangGraph StateGraph for the chatbot.

    Args:
        session: Database session for tools

    Returns:
        Compiled StateGraph
    """
    # Create tools with database session
    tools = create_pizza_tools(session)

    # Initialize the graph
    workflow = StateGraph(ChatbotState)

    # Add nodes with async wrappers
    async def llm_wrapper(state):
        return await llm_decision_node(state, tools)

    async def tool_wrapper(state):
        return await tool_execution_node(state, tools)

    # workflow.add_node("greeting", greeting_node)  # Disabled - greeting handled by frontend
    workflow.add_node("llm_decision", llm_wrapper)
    workflow.add_node("tool_execution", tool_wrapper)
    workflow.add_node("state_update", state_update_node)

    # Define edges (conversation flow)
    workflow.set_entry_point("llm_decision")  # Start directly with LLM

    # workflow.add_edge("greeting", "llm_decision")  # Disabled

    # Conditional edge: if tool is needed, execute it; otherwise update state
    def should_use_tool(state: ChatbotState) -> str:
        """Decide whether to execute a tool or proceed"""
        messages = state.get("messages", [])

        # Check if last message has tool_calls
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "assistant" and last_msg.get("tool_calls"):
                return "tool_execution"

        return "state_update"

    workflow.add_conditional_edges(
        "llm_decision",
        should_use_tool,
        {
            "tool_execution": "tool_execution",
            "state_update": "state_update"
        }
    )

    # Loop back to LLM after tool execution to process result
    workflow.add_edge("tool_execution", "llm_decision")
    workflow.add_edge("state_update", END)

    # Compile the graph
    app = workflow.compile()

    logger.info("Chatbot graph compiled successfully")

    return app
