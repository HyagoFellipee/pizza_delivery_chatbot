"""
LangChain tools for pizza operations.
"""
from langchain.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.services.pizza_service import PizzaService

logger = logging.getLogger(__name__)


def create_pizza_tools(session: AsyncSession):
    """
    Create pizza-related tools with database session.

    Args:
        session: Database session

    Returns:
        List of LangChain tools
    """
    pizza_service = PizzaService(session)

    @tool
    async def get_pizza_price(pizza_name: str) -> str:
        """
        Get the price of a specific pizza from the menu.

        Args:
            pizza_name: The name of the pizza (e.g., "Margherita", "Pepperoni")

        Returns:
            A string with the price information or error message
        """
        try:
            pizza = await pizza_service.get_pizza_by_name(pizza_name)

            if pizza:
                return f"A pizza {pizza.name} custa R$ {pizza.price:.2f}. Ingredientes: {pizza.ingredients}"
            else:
                # Try to list similar pizzas
                all_pizzas = await pizza_service.get_all_pizzas()
                pizza_names = [p.name for p in all_pizzas]
                return f"Desculpe, não encontrei uma pizza chamada '{pizza_name}'. Pizzas disponíveis: {', '.join(pizza_names)}"

        except Exception as e:
            logger.error(f"Error getting pizza price: {e}")
            return f"Desculpe, encontrei um erro ao buscar o preço da pizza."

    @tool
    async def list_all_pizzas() -> str:
        """
        List all available pizzas with their prices.

        Returns:
            A formatted string with all pizzas and prices
        """
        try:
            all_pizzas = await pizza_service.get_all_pizzas()

            if not all_pizzas:
                return "Desculpe, não há pizzas disponíveis no momento."

            pizza_list = "\n".join([
                f"- {pizza.name}: R$ {pizza.price:.2f}"
                for pizza in all_pizzas
            ])

            return f"Aqui estão nossas pizzas disponíveis:\n{pizza_list}"

        except Exception as e:
            logger.error(f"Error listing pizzas: {e}")
            return "Desculpe, encontrei um erro ao buscar a lista de pizzas."

    return [get_pizza_price, list_all_pizzas]
