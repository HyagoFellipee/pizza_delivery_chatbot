"""
Pizza service for database operations.
"""
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from app.models.pizza import Pizza

logger = logging.getLogger(__name__)


class PizzaService:
    """Service for pizza-related operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pizza_by_name(self, name: str) -> Optional[Pizza]:
        """
        Get pizza by name (case-insensitive).

        Args:
            name: Pizza name

        Returns:
            Pizza object or None if not found
        """
        statement = select(Pizza).where(Pizza.name.ilike(f"%{name}%"))
        result = await self.session.execute(statement)
        pizza = result.scalars().first()
        return pizza

    async def get_all_pizzas(self) -> List[Pizza]:
        """
        Get all available pizzas.

        Returns:
            List of all pizzas
        """
        statement = select(Pizza)
        result = await self.session.execute(statement)
        pizzas = result.scalars().all()
        return list(pizzas)

    async def get_pizza_price(self, name: str) -> Optional[float]:
        """
        Get price for a specific pizza.

        Args:
            name: Pizza name

        Returns:
            Price or None if pizza not found
        """
        pizza = await self.get_pizza_by_name(name)
        return pizza.price if pizza else None
