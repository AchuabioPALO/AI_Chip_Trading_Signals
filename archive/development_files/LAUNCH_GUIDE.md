# 🚀 AI Chip Trading Signal System - Launch Guide

## Quick Launch (Automated)

**Option 1: One-Command Launch**
```bash
cd /Users/achuabio/AI_Chip_Trading_Signals
./launch_system.sh
```

This script will automatically:
- ✅ Set up environment variables
- ✅ Start backend on port 8000
- ✅ Start frontend on port 3000  
- ✅ Monitor both processes
- ✅ Auto-restart if they crash

---

## Manual Launch (Step-by-Step)

### 📋 Prerequisites
```bash
# Ensure you're in the project directory
cd /Users/achuabio/AI_Chip_Trading_Signals

# Activate virtual environment
source venv/bin/activate

# Install missing dependencies
pip install httpx
pip install -e .
```

### 🔧 Backend Launch (Terminal 1)

```bash
# Terminal 1 - Backend
cd /Users/achuabio/AI_Chip_Trading_Signals

# Set environment
export PYTHONPATH="${PWD}/backend/src:${PYTHONPATH}"
# FRED_API_KEY is loaded from .env file automatically

# Create directories
mkdir -p backend/data backend/logs

# Start FastAPI server
cd backend/src
python main.py
```

**Backend URLs:**
- 🔗 Health Check: http://localhost:8000/
- 📖 API Docs: http://localhost:8000/docs
- 📊 Market Data: http://localhost:8000/api/market-data
- 💎 Chip Signals: http://localhost:8000/api/chip-signals

### 🎨 Frontend Launch (Terminal 2)

```bash
# Terminal 2 - Frontend
cd /Users/achuabio/AI_Chip_Trading_Signals/recession_tracker

# Install dependencies (first time only)
npm install

# Start Next.js development server
npm run dev
```

**Frontend URLs:**
- 🌐 Dashboard: http://localhost:3000/
- 📊 Live signals with real-time updates
- 📈 Interactive bond stress indicators

---

## 🔍 Verification Steps

### 1. Backend Health Check
```bash
curl http://localhost:8000/
# Expected: {"message": "AI Chip Trading Signal API is running"}
```

### 2. API Endpoints Test
```bash
# Test market data endpoint
curl http://localhost:8000/api/market-data

# Test chip signals
curl http://localhost:8000/api/chip-signals
```

### 3. Frontend Access
- Open browser: http://localhost:3000/
- Should see AI Chip Trading Dashboard
- Real-time signal updates from backend API

---

## 🛠️ Troubleshooting

### Backend Issues

**Port 8000 in use:**
```bash
# Kill existing process
lsof -ti :8000 | xargs kill -9
```

**Import errors:**
```bash
# Reinstall package in development mode
pip install -e .
```

**Database issues:**
```bash
# Reset database
rm backend/data/trading_signals.db
# Restart backend - it will recreate tables
```

### Frontend Issues

**Port 3000 in use:**
```bash
# Kill existing process
lsof -ti :3000 | xargs kill -9
```

**Dependencies issues:**
```bash
cd recession_tracker
rm -rf node_modules package-lock.json
npm install
```

**API connection issues:**
- Ensure backend is running on port 8000
- Check CORS settings in backend/src/main.py

---

## 📊 What You'll See

### Backend Console Output:
```
INFO: Starting AI Chip Trading Signal API
INFO: Enhanced update complete: Bond signal strength = SOON
INFO: Generated 3 chip signals, Sent 1 high-priority alerts
INFO: Uvicorn running on http://localhost:8000
```

### Frontend Console Output:
```
▲ Next.js 15.3.4
- Local:        http://localhost:3000
- turbopack (alpha)

✓ Ready in 2.1s
```

### Dashboard Features:
- 📊 **Real-time Bond Stress Indicators**
- 💎 **AI Chip Trading Signals** (NVDA, AMD, TSM)
- 📈 **Multi-timeframe Analysis** (20D/40D/60D)
- 🎯 **Position Sizing Recommendations**
- 📱 **Mobile-responsive Interface**

---

## 🔄 Development Workflow

1. **Start both services** using automated script or manual steps
2. **Backend changes** - Server auto-reloads with FastAPI
3. **Frontend changes** - Hot reload with Next.js
4. **API testing** - Use http://localhost:8000/docs
5. **Database inspection** - SQLite browser or DB tools

---

## 🎯 Ready for Trading!

Once both services are running:
- ✅ Real-time signal generation every 5 minutes
- ✅ ML-powered bond stress analysis  
- ✅ VIX-based position sizing
- ✅ Multi-timeframe correlation tracking
- ✅ Automated notifications (if configured)
- ✅ Historical performance validation

**Status: Production-ready AI trading signal system! 🚀**
