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
        "name": "Margherita Classica",
        "ingredients": "tomato sauce, mozzarella, fresh basil, olive oil",
        "price": 12.99
    },
    {
        "name": "Pepperoni Supreme",
        "ingredients": "tomato sauce, mozzarella, pepperoni, oregano",
        "price": 14.99
    },
    {
        "name": "Quattro Formaggi",
        "ingredients": "mozzarella, gorgonzola, parmesan, fontina cheese",
        "price": 16.99
    },
    {
        "name": "Vegetariana Deluxe",
        "ingredients": "tomato sauce, mozzarella, bell peppers, mushrooms, onions, olives, tomatoes",
        "price": 15.99
    },
    {
        "name": "Hawaiian Paradise",
        "ingredients": "tomato sauce, mozzarella, ham, pineapple",
        "price": 13.99
    },
    {
        "name": "BBQ Chicken Feast",
        "ingredients": "BBQ sauce, mozzarella, grilled chicken, red onions, cilantro",
        "price": 17.99
    },
    {
        "name": "Meat Lovers Special",
        "ingredients": "tomato sauce, mozzarella, pepperoni, sausage, bacon, ham",
        "price": 18.99
    },
    {
        "name": "Mediterranean Dream",
        "ingredients": "tomato sauce, mozzarella, feta cheese, olives, sun-dried tomatoes, artichokes",
        "price": 16.49
    },
    {
        "name": "Spicy Diavola",
        "ingredients": "tomato sauce, mozzarella, spicy salami, hot peppers, chili flakes",
        "price": 15.49
    },
    {
        "name": "Truffle Mushroom Gourmet",
        "ingredients": "white sauce, mozzarella, mixed mushrooms, truffle oil, parmesan",
        "price": 19.99
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
