#!/usr/bin/env python3
"""
Quick Backend Startup Test
Tests the backend components and starts the server
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))
os.chdir('backend/src')

def test_backend_components():
    """Test all backend components before startup"""
    print("🧪 Testing Backend Components...")
    
    try:
        # Test FRED client
        from data_sources.fred_client import FredClient
        fred = FredClient()
        print("✅ FRED client imported")
        
        # Test with real API key
        data = fred.get_yield_curve_data()
        print(f"✅ FRED API working: {len(data) if data else 0} data points")
        
        # Test Yahoo client
        from data_sources.yahoo_client import YahooFinanceClient
        yahoo = YahooFinanceClient()
        print("✅ Yahoo Finance client imported")
        
        # Test signal analyzers
        from signals.bond_stress_analyzer import BondStressAnalyzer
        from signals.correlation_engine import CorrelationEngine
        from signals.signal_generation_engine import SignalGenerationEngine
        print("✅ Signal engines imported")
        
        # Test database
        from utils.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database manager imported")
        
        # Test FastAPI app
        from main import app
        print("✅ FastAPI app imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_backend_server():
    """Start the backend server"""
    print("\n🚀 Starting Backend Server...")
    
    try:
        import uvicorn
        from main import app
        
        print("📊 API will be available at: http://localhost:8000")
        print("📖 API docs at: http://localhost:8000/docs")
        print("🔄 Starting server...")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 AI Chip Trading Signal System - Backend Startup")
    print("=" * 60)
    
    # Test components first
    if test_backend_components():
        print("\n✅ All components tested successfully!")
        start_backend_server()
    else:
        print("\n❌ Component tests failed. Please fix issues before starting server.")
        sys.exit(1)
