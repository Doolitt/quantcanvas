# QuantCanvas

> AI-powered investment strategy platform with economic data, backtesting, and portfolio tracking

## 🎯 Features

- **Economic Calendar** - Real-time economic indicators (CPI, NFP, Fed speeches)
- **Portfolio Tracker** - Track TradFi, Crypto, and hybrid portfolios
- **Strategy Builder** - Create, backtest, and optimize investment strategies
- **AI Analysis** - Economic insights and strategy suggestions powered by AI agents
- **Web3 Integration** - Connect wallets to track on-chain positions

## 🏗️ Architecture

### Frontend
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS v4
- shadcn/ui components

### Backend
- FastAPI (Python) / Next.js API routes
- PostgreSQL (Supabase)
- Redis (Upstash)

### Data Sources
- Economic: Econoday, FRED API
- Market: Yahoo Finance, CoinGecko
- On-chain: Alchemy, Moralis

### AI Layer
- Ultra-budget agent system ($5/day)
- Specialized agents for economic analysis, portfolio optimization
- Gemini Flash 3.0, DeepSeek V3, Minimax 2.5

## 🚀 Getting Started

### Development
```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

### Environment Variables
```bash
# Create .env.local
NEXT_PUBLIC_SUPABASE_URL=your_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key
```

## 📊 Database Schema

See `quantcanvas-docs/database-schema.md` for full PostgreSQL schema.

## 🤖 AI Agent System

QuantCanvas uses a multi-agent AI system:
- **Rex** - Main orchestrator
- **Chronos** - Calendar/economic specialist
- **Quant** - Strategy backtesting agent
- **Oracle** - Economic analysis agent

## 📅 Roadmap

### MVP (April 2026)
- [x] Next.js project setup
- [ ] Basic dashboard layout
- [ ] Economic calendar integration
- [ ] Portfolio tracker UI
- [ ] Strategy builder interface
- [ ] Backtesting engine integration

### Phase 2
- [ ] Web3 wallet integration
- [ ] AI analysis dashboard
- [ ] Strategy marketplace
- [ ] Mobile responsive design

## 🔧 Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, PostgreSQL, Redis
- **AI**: OpenRouter, Gemini, DeepSeek, Minimax
- **Infra**: Vercel, Supabase, Upstash
- **Tools**: OpenClaw agent framework