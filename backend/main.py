"""
FastAPI main application entry point for Pizza Delivery Chatbot.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.connection import init_db
from app.database.seed import seed_database
from app.routers import health, chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database and seed data
    logger.info("Starting up Pizza Delivery Chatbot API...")
    try:
        await init_db()
        await seed_database()
        logger.info("Database initialized and seeded successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Pizza Delivery Chatbot API...")


# Initialize FastAPI app
app = FastAPI(
    title="Pizza Delivery Chatbot API",
    description="Conversational AI chatbot for pizza ordering using LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pizza Delivery Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }
