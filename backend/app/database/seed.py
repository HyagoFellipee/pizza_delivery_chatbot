"""
Database seeding script for fictional pizza data.
"""
from sqlmodel import select
from typing import List
import logging

from app.database.connection import async_session
from app.models.pizza import Pizza

logger = logging.getLogger(__name__)


SEED_PIZZAS: List[dict] = [
    {
        "name": "Margherita",
        "ingredients": "molho de tomate, mussarela, manjericão fresco, azeite",
        "price": 35.90
    },
    {
        "name": "Calabresa",
        "ingredients": "molho de tomate, mussarela, calabresa, cebola, azeitonas",
        "price": 39.90
    },
    {
        "name": "Quatro Queijos",
        "ingredients": "mussarela, gorgonzola, parmesão, provolone",
        "price": 45.90
    },
    {
        "name": "Portuguesa",
        "ingredients": "molho de tomate, mussarela, presunto, ovos, cebola, azeitonas, ervilha",
        "price": 42.90
    },
    {
        "name": "Frango com Catupiry",
        "ingredients": "molho de tomate, mussarela, frango desfiado, catupiry",
        "price": 43.90
    },
    {
        "name": "Bacon",
        "ingredients": "molho de tomate, mussarela, bacon, cebola",
        "price": 41.90
    },
    {
        "name": "Vegetariana",
        "ingredients": "molho de tomate, mussarela, pimentão, champignon, cebola, azeitonas, tomate",
        "price": 40.90
    },
    {
        "name": "Napolitana",
        "ingredients": "molho de tomate, mussarela, tomate fresco, parmesão, manjericão",
        "price": 38.90
    },
    {
        "name": "Lombo Canadense",
        "ingredients": "molho de tomate, mussarela, lombo canadense, catupiry",
        "price": 44.90
    },
    {
        "name": "Especial da Casa",
        "ingredients": "molho de tomate, mussarela, calabresa, bacon, champignon, milho, azeitonas",
        "price": 47.90
    }
]


async def seed_database() -> None:
    """
    Seed the database with fictional pizza data.
    Only seeds if the database is empty.
    """
    async with async_session() as session:
        # Check if pizzas already exist
        result = await session.execute(select(Pizza))
        existing_pizzas = result.scalars().all()

        if existing_pizzas:
            logger.info(f"Database already seeded with {len(existing_pizzas)} pizzas")
            return

        # Seed pizzas
        logger.info("Seeding database with pizza data...")
        for pizza_data in SEED_PIZZAS:
            pizza = Pizza(**pizza_data)
            session.add(pizza)

        await session.commit()
        logger.info(f"Successfully seeded {len(SEED_PIZZAS)} pizzas")
