#!/usr/bin/env python3
"""
Simple verification that all imports work correctly
"""

import sys
import os

# Add the backend src directory to Python path
backend_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'src')
sys.path.insert(0, backend_src)

try:
    from data_sources.fred_client import FredClient
    print("✅ FredClient imported")
except ImportError as e:
    print(f"❌ FredClient import failed: {e}")

try:
    from data_sources.yahoo_client import YahooFinanceClient
    print("✅ YahooFinanceClient imported")
except ImportError as e:
    print(f"❌ YahooFinanceClient import failed: {e}")

try:
    from signals.bond_stress_analyzer import BondStressAnalyzer, BondStressSignal, SignalStrength
    print("✅ BondStressAnalyzer components imported")
except ImportError as e:
    print(f"❌ BondStressAnalyzer import failed: {e}")

try:
    from signals.correlation_engine import CorrelationEngine
    print("✅ CorrelationEngine imported")
except ImportError as e:
    print(f"❌ CorrelationEngine import failed: {e}")

try:
    from models.ml_signal_engine import MLSignalEngine
    print("✅ MLSignalEngine imported")
except ImportError as e:
    print(f"❌ MLSignalEngine import failed: {e}")

try:
    from utils.database import DatabaseManager
    print("✅ DatabaseManager imported")
except ImportError as e:
    print(f"❌ DatabaseManager import failed: {e}")

try:
    from utils.config import Config
    print("✅ Config imported")
except ImportError as e:
    print(f"❌ Config import failed: {e}")

try:
    from utils.alert_system import DiscordAlertSystem, EmailAlertSystem
    print("✅ Alert systems imported")
except ImportError as e:
    print(f"❌ Alert systems import failed: {e}")

print("\n🎯 Import verification complete!")
