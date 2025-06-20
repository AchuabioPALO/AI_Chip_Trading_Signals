import os
from typing import Dict, List
import logging

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: str = "logs/trading_signals.log"):
	"""Setup logging configuration"""
	
	# Create logs directory if it doesn't exist
	os.makedirs(os.path.dirname(log_file), exist_ok=True)
	
	logging.basicConfig(
		level=getattr(logging, log_level.upper()),
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
		handlers=[
			logging.FileHandler(log_file),
			logging.StreamHandler()
		]
	)

# API Configuration
class Config:
	"""Application configuration"""
	
	# API Keys (use environment variables in production)
	FRED_API_KEY = os.getenv("FRED_API_KEY", "demo_key")
	
	# Database
	DATABASE_PATH = os.getenv("DATABASE_PATH", "data/trading_signals.db")
	
	# Data Update Intervals (seconds)
	DATA_UPDATE_INTERVAL = int(os.getenv("DATA_UPDATE_INTERVAL", "300"))  # 5 minutes
	CACHE_TTL = int(os.getenv("CACHE_TTL", "1800"))  # 30 minutes
	
	# Trading Parameters
	AI_CHIP_SYMBOLS = ["NVDA", "AMD", "TSM", "INTC", "QCOM"]
	BOND_ETFS = ["TLT", "IEF", "SHY", "HYG", "LQD"]
	
	# Signal Thresholds
	ZSCORE_THRESHOLDS = {
		"strong": 2.0,
		"moderate": 1.5,
		"weak": 1.0
	}
	
	CORRELATION_THRESHOLDS = {
		"strong_negative": -0.3,
		"moderate_negative": -0.2,
		"neutral": 0.2,
		"positive": 0.3
	}
	
	# Risk Management
	MAX_POSITION_SIZE = 0.25  # 25% max position
	BASE_POSITION_SIZE = 0.10  # 10% base position
	DEFAULT_STOP_LOSS = 0.05   # 5% stop loss
	DEFAULT_TAKE_PROFIT = 0.10  # 10% take profit
	
	# Notification Settings
	SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
	TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
	TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
	
	# API Rate Limiting
	FRED_RATE_LIMIT = 0.5  # 0.5 seconds between calls
	YAHOO_RATE_LIMIT = 0.1  # 0.1 seconds between calls
	
	@classmethod
	def get_required_env_vars(cls) -> List[str]:
		"""Get list of required environment variables for production"""
		return [
			"FRED_API_KEY",
			"SLACK_WEBHOOK_URL",
			"TELEGRAM_BOT_TOKEN",
			"TELEGRAM_CHAT_ID"
		]
	
	@classmethod
	def validate_config(cls) -> Dict[str, bool]:
		"""Validate configuration for production readiness"""
		validation = {}
		
		for var in cls.get_required_env_vars():
			validation[var] = os.getenv(var) is not None
		
		return validation

# Initialize logging
setup_logging()
