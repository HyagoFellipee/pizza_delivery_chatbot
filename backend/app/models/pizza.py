"""
SQLModel Pizza model.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Pizza(SQLModel, table=True):
    """
    Pizza model representing available pizzas in the menu.
    """
    __tablename__ = "pizzas"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=100)
    ingredients: str = Field(max_length=500)
    price: float = Field(gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Margherita Classica",
                "ingredients": "tomato sauce, mozzarella, fresh basil, olive oil",
                "price": 12.99
            }
        }
