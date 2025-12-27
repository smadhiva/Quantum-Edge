# Quantum-Edge
# 💰 Finance Portfolio Copilot

**Live, Multi-Threaded, Agentic Investment Intelligence powered by Pathway + Gemini**

A live financial co-pilot where users can create multiple independent portfolio threads, each handled by a multi-agent system that continuously analyzes market prices, company fundamentals, peer comparisons, and live news using Pathway's streaming document indexing.

## 🚀 Features

- **Live Data Streaming**: Real-time market prices, news, and document updates
- **Multi-Agent System**: Specialized agents for different financial analysis tasks
- **Portfolio Management**: Create and manage multiple independent portfolios
- **RAG with Pathway**: Always up-to-date context using streaming RAG
- **Gemini LLM**: Advanced reasoning and analysis capabilities

## 🏗️ Architecture

```
Frontend (React / Next.js)
   |
   | REST / WebSocket
   v
FastAPI Backend
   |
   | orchestrates agents
   v
Agent Layer (LangGraph)
   |
   | RAG queries
   v
Pathway Streaming Engine
   |
   | live embeddings
   v
Gemini LLM (Analysis + Reasoning)
```

## 📁 Project Structure

```
finance-copilot/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── agents/                 # Multi-agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Base agent class
│   │   ├── auth_agent.py       # Authentication agent
│   │   ├── portfolio_agent.py  # Portfolio management
│   │   ├── equity_agent.py     # Equity research
│   │   ├── news_agent.py       # News intelligence
│   │   ├── risk_agent.py       # Risk profiling
│   │   ├── market_agent.py     # Market trends
│   │   └── orchestrator.py     # Agent orchestration
│   ├── pathway/                # Pathway streaming components
│   │   ├── __init__.py
│   │   ├── ingestion.py        # Document ingestion
│   │   ├── streams.py          # Data streams
│   │   └── vector_store.py     # Vector store setup
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── market_data.py      # Market data fetching
│   │   ├── news_service.py     # News aggregation
│   │   └── portfolio_service.py
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── portfolio.py
│   │   ├── stock.py
│   │   └── user.py
│   └── routes/                 # API routes
│       ├── __init__.py
│       ├── portfolio.py
│       ├── analysis.py
│       └── auth.py
├── frontend/                   # React/Next.js frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── data/                       # Data storage
│   ├── docs/                   # Financial documents
│   ├── prices/                 # Price data
│   └── portfolios/             # User portfolios
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Cloud API Key (for Gemini)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
DATABASE_URL=sqlite:///./finance_copilot.db
```

## 🚀 Running the Application

### Start Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

### Start Pathway Pipeline

```bash
cd backend
python -m pathway.run
```

## 🤖 Agents

| Agent | Purpose |
|-------|---------|
| Auth Agent | Login & session management |
| Portfolio Thread Agent | Create & isolate portfolios |
| Risk Profiling Agent | Assess goals, horizon, appetite |
| Asset Allocation Agent | MF / ETF / Bonds allocation |
| Equity Research Agent | Fundamentals & valuation |
| Market Trend Agent | Price + indicators analysis |
| Peer Comparison Agent | Competitors & investors |
| News Intelligence Agent | Live news summarization |
| Visualization Agent | Charts + reports generation |
| Portfolio Monitor Agent | Buy/sell updates tracking |

## 📊 Demo Script

1. **Upload new quarterly report** → Watch recommendation change
2. **Update portfolio CSV** → P&L recalculates instantly
3. **Market price changes** → Charts update in real-time
4. **News article added** → Sentiment analysis shifts

⚠️ No refresh. No restart. Everything is LIVE!

## 🏆 Hackathon Track

**Track-1: Agentic AI with Live Data**

## 📝 License

MIT License
