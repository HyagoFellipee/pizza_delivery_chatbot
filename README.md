# Pizza Delivery Chatbot

A conversational AI chatbot for pizza ordering built with FastAPI, LangGraph, React, and PostgreSQL.

## Features

- Conversational interface for ordering pizzas
- Real-time price checking using LangChain tools
- Stateful conversation management with LangGraph
- PostgreSQL database with auto-seeded pizza menu
- React + TypeScript frontend with Tailwind CSS
- Docker Compose for one-command deployment

## Tech Stack

**Backend:**
- FastAPI (async/await)
- SQLModel ORM
- LangGraph (StateGraph)
- LangChain Tools
- PostgreSQL
- Groq API (LLM)

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Axios

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL 15

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Groq API key (free tier: https://console.groq.com/)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/HyagoFellipee/pizza_delivery_chatbot.git
cd pizza_delivery_chatbot
```

2. Copy environment template and configure:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

3. Start all services with Docker Compose:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:5174
- Backend API: http://localhost:8004
- API Docs: http://localhost:8004/docs

### Environment Variables

See `.env.example` for all available configuration options.

Required:
- `GROQ_API_KEY`: Your Groq API key

## Development

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Project Structure

```
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── database/    # Database connection & seeding
│   │   ├── models/      # SQLModel models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── tools/       # LangChain tools
│   │   └── graph/       # LangGraph StateGraph
│   └── main.py
│
└── frontend/         # React frontend
    └── src/
        ├── components/  # React components
        ├── services/    # API client
        └── types/       # TypeScript types
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/chat` - Send chat message

## Database

PostgreSQL database is auto-seeded with 10 fictional pizzas on startup.

## License

MIT License - see LICENSE file for details.
