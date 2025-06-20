# AI Chip Trading Signal Dashboard

This is a [Next.js](https://nextjs.org) trading dashboard for monitoring bond market stress indicators and generating AI semiconductor trading signals. Built for quantitative traders and portfolio managers.

## Features

- **Real-time Bond Market Monitoring**: 10Y-2Y yield curve, MOVE index, credit spreads
- **AI Chip Trading Signals**: NVDA, AMD, TSM position recommendations  
- **Risk Management**: Automated position sizing and stop-loss suggestions
- **Mobile-First Design**: PWA capabilities for trading on the go
- **Real-time Updates**: WebSocket connections for live market data

## Getting Started

First, install dependencies and run the development server:

```bash
npm install
npm run dev
# or
yarn install && yarn dev
# or
pnpm install && pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the trading dashboard.

## Technology Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Charts**: Chart.js with react-chartjs-2 for financial visualizations
- **Real-time Data**: WebSocket connections with React Query for state management
- **Deployment**: Optimized for Vercel with edge functions

## Architecture

```
Frontend (Next.js) ← WebSocket → Python Backend (Bond Analysis)
      ↓                              ↓
   Real-time UI              Financial APIs (Fed, Yahoo Finance)
```
