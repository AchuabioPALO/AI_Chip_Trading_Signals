#!/usr/bin/env python3
"""
Simple scheduler for bond stress monitoring data updates
Executes tasks autonomously as per Feature 01 requirements
"""

import schedule
import time
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend' / 'src'
sys.path.insert(0, str(backend_path))

# Also add current directory
current_path = Path(__file__).parent
sys.path.insert(0, str(current_path))

from data_sources.fred_client import FredClient
from data_sources.yahoo_client import YahooFinanceClient
from signals.bond_stress_analyzer import BondStressAnalyzer
from signals.correlation_engine import CorrelationEngine
from utils.database import DatabaseManager
from utils.alert_system import DiscordAlertSystem, EmailAlertSystem

# Setup logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler('logs/scheduler.log'),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

class BondStressScheduler:
	"""Autonomous scheduler for bond stress monitoring tasks"""
	
	def __init__(self):
		self.fred_client = FredClient()
		self.yahoo_client = YahooFinanceClient()
		self.bond_analyzer = BondStressAnalyzer()
		self.correlation_engine = CorrelationEngine()
		self.db = DatabaseManager()
		
		# Alert systems (Feature 01 requirements)
		self.discord_alerts = DiscordAlertSystem()
		self.email_alerts = EmailAlertSystem()
		
		# Ensure directories exist
		os.makedirs('data', exist_ok=True)
		os.makedirs('logs', exist_ok=True)
		
	def collect_bond_data(self):
		"""Task: Collect and process bond market stress data"""
		logger.info("🔄 Starting bond data collection...")
		
		try:
			# Get treasury yield data (FRED API Task)
			yield_data = self.fred_client.get_yield_curve_data()
			
			# Get bond ETF data (yfinance integration task)
			bond_etf_data = self.yahoo_client.get_bond_etf_data()
			
			# Get VIX as MOVE index proxy (task requirement)
			vix_data = self.yahoo_client.get_vix_data()
			
			# Calculate yield curve spread and z-scores (yield curve module task)
			if yield_data and '10Y' in yield_data and '2Y' in yield_data:
				spread = self.fred_client.calculate_yield_spread(yield_data)
				
				# Calculate bond volatility and credit spreads
				volatility = self.bond_analyzer.calculate_bond_volatility(bond_etf_data)
				credit_spreads = self.bond_analyzer.calculate_credit_spreads(bond_etf_data)
				
				# Generate stress signal
				signal = self.bond_analyzer.generate_stress_signal(
					spread['spread'], volatility, credit_spreads
				)
				
				# Store in database (SQLite task)
				self.db.store_bond_signal(signal)
				
				# CSV backup (data backup task)
				self.backup_to_csv(signal, spread, volatility, credit_spreads)
				
				logger.info(f"✅ Bond data collected. Signal: {signal.signal_strength.value}")
				
				# Check for alerts
				if signal.confidence_score >= 7.0:
					self.send_alerts(signal)
				
			else:
				logger.warning("⚠️  Insufficient yield data for analysis")
				
		except Exception as e:
			logger.error(f"❌ Bond data collection failed: {e}")
	
	def collect_chip_data(self):
		"""Task: Collect AI chip stock data and calculate correlations"""
		logger.info("🔄 Starting chip data collection...")
		
		try:
			# Get AI chip stock data
			chip_data = self.yahoo_client.get_ai_chip_stocks()
			
			# Get latest bond signal for correlation
			latest_bond = self.db.get_latest_bond_signal()
			
			if chip_data and latest_bond:
				# Calculate correlations (basic correlation task)
				bond_data = self.yahoo_client.get_bond_etf_data()
				
				for symbol, data in chip_data.items():
					if not data.empty and 'TLT' in bond_data:
						chip_returns = data['Close'].pct_change().dropna()
						bond_returns = bond_data['TLT']['Close'].pct_change().dropna()
						
						correlation = self.correlation_engine.calculate_bond_chip_correlation(
							bond_returns, chip_returns
						)
						
						# Store correlation data
						self.db.cache_market_data('correlation', {
							'symbol': symbol,
							'correlation': correlation,
							'timestamp': datetime.now()
						})
				
				logger.info(f"✅ Chip data collected for {len(chip_data)} stocks")
			
		except Exception as e:
			logger.error(f"❌ Chip data collection failed: {e}")
	
	def backup_to_csv(self, signal, spread, volatility, credit_spreads):
		"""CSV data backup task"""
		try:
			import pandas as pd
			
			# Create backup data
			backup_data = {
				'timestamp': datetime.now(),
				'yield_spread': signal.yield_curve_spread,
				'yield_zscore': signal.yield_curve_zscore,
				'bond_volatility': signal.bond_volatility,
				'credit_spreads': signal.credit_spreads,
				'signal_strength': signal.signal_strength.value,
				'confidence': signal.confidence_score
			}
			
			# Append to CSV
			df = pd.DataFrame([backup_data])
			csv_file = 'data/bond_stress_backup.csv'
			
			if os.path.exists(csv_file):
				df.to_csv(csv_file, mode='a', header=False, index=False)
			else:
				df.to_csv(csv_file, index=False)
			
			logger.info("✅ Data backed up to CSV")
			
		except Exception as e:
			logger.error(f"❌ CSV backup failed: {e}")
	
	def send_alerts(self, signal):
		"""Alert system task - Discord webhook and email implementation"""
		try:
			# Simple logging alert (basic logging task)
			logger.warning(f"🚨 BOND STRESS ALERT: {signal.signal_strength.value} - {signal.suggested_action}")
			
			# Discord webhook alert (Feature 01 requirement)
			discord_sent = self.discord_alerts.send_sync_alert(signal)
			if discord_sent:
				logger.info("✅ Discord alert sent")
			
			# Email alert for critical signals (Feature 01 requirement)
			if signal.confidence_score >= 8.0:
				email_sent = self.email_alerts.send_critical_alert(signal)
				if email_sent:
					logger.info("✅ Critical email alert sent")
			
		except Exception as e:
			logger.error(f"❌ Alert system failed: {e}")
	
	def start_scheduler(self):
		"""Start the autonomous scheduler"""
		logger.info("🚀 Starting Bond Stress Monitoring Scheduler")
		
		# Schedule tasks as per Feature 01 requirements
		schedule.every(30).minutes.do(self.collect_bond_data)  # 30-min updates
		schedule.every(30).minutes.do(self.collect_chip_data)
		
		# Daily backup and cleanup
		schedule.every().day.at("00:00").do(self.daily_maintenance)
		
		# Run initial collection
		self.collect_bond_data()
		self.collect_chip_data()
		
		logger.info("📋 Scheduler started. Tasks running every 30 minutes.")
		
		# Keep running
		while True:
			schedule.run_pending()
			time.sleep(60)  # Check every minute
	
	def daily_maintenance(self):
		"""Daily maintenance tasks"""
		logger.info("🔧 Running daily maintenance...")
		
		try:
			# Clean old data (keep last 90 days)
			# Compress old logs
			# Validate data integrity
			pass
			
		except Exception as e:
			logger.error(f"❌ Daily maintenance failed: {e}")

def main():
	"""Main entry point for autonomous execution"""
	scheduler = BondStressScheduler()
	
	try:
		scheduler.start_scheduler()
	except KeyboardInterrupt:
		logger.info("🛑 Scheduler stopped by user")
	except Exception as e:
		logger.error(f"❌ Scheduler crashed: {e}")

if __name__ == "__main__":
	main()
