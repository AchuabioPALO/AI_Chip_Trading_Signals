import sqlite3
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from signals.bond_stress_analyzer import BondStressSignal
from signals.correlation_engine import ChipTradingSignal

class DatabaseManager:
	"""SQLite database manager for storing trading signals and market data"""
	
	def __init__(self, db_path: str = None):
		if db_path is None:
			# Get the absolute path to the database file
			current_dir = Path(__file__).parent.parent.parent  # Go up to project root
			self.db_path = str(current_dir / "backend" / "data" / "trading_signals.db")
		else:
			self.db_path = db_path
		
		# Ensure the directory exists
		os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
		
		self.logger = logging.getLogger(__name__)
		self.logger.info(f"Database path: {self.db_path}")
		self._create_tables()
	
	def _create_tables(self):
		"""Create database tables if they don't exist"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				# Bond stress signals table
				cursor.execute("""
					CREATE TABLE IF NOT EXISTS bond_stress_signals (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						timestamp DATETIME NOT NULL,
						yield_curve_spread REAL,
						yield_curve_zscore REAL,
						bond_volatility REAL,
						credit_spreads REAL,
						signal_strength TEXT,
						confidence_score REAL,
						suggested_action TEXT,
						created_at DATETIME DEFAULT CURRENT_TIMESTAMP
					)
				""")
				
				# Chip trading signals table
				cursor.execute("""
					CREATE TABLE IF NOT EXISTS chip_trading_signals (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						timestamp DATETIME NOT NULL,
						symbol TEXT NOT NULL,
						signal_type TEXT,
						signal_strength TEXT,
						confidence_score REAL,
						target_horizon_days INTEGER,
						bond_correlation REAL,
						suggested_position_size REAL,
						entry_price REAL,
						stop_loss REAL,
						take_profit REAL,
						reasoning TEXT,
						created_at DATETIME DEFAULT CURRENT_TIMESTAMP
					)
				""")
				
				# Market data cache table
				cursor.execute("""
					CREATE TABLE IF NOT EXISTS market_data_cache (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						data_type TEXT NOT NULL,
						symbol TEXT,
						timestamp DATETIME NOT NULL,
						data_json TEXT,
						created_at DATETIME DEFAULT CURRENT_TIMESTAMP
					)
				""")
				
				# Performance tracking table
				cursor.execute("""
					CREATE TABLE IF NOT EXISTS signal_performance (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						signal_id INTEGER,
						symbol TEXT,
						entry_date DATETIME,
						exit_date DATETIME,
						entry_price REAL,
						exit_price REAL,
						return_pct REAL,
						holding_days INTEGER,
						signal_type TEXT,
						created_at DATETIME DEFAULT CURRENT_TIMESTAMP
					)
				""")
				
				conn.commit()
				self.logger.info("Database tables created successfully")
				
		except Exception as e:
			self.logger.error(f"Error creating database tables: {e}")
	
	def store_bond_signal(self, signal: BondStressSignal):
		"""Store bond stress signal in database"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cursor.execute("""
					INSERT INTO bond_stress_signals 
					(timestamp, yield_curve_spread, yield_curve_zscore, bond_volatility, 
					 credit_spreads, signal_strength, confidence_score, suggested_action)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?)
				""", (
					signal.timestamp,
					signal.yield_curve_spread,
					signal.yield_curve_zscore,
					signal.bond_volatility,
					signal.credit_spreads,
					signal.signal_strength.value,
					signal.confidence_score,
					signal.suggested_action
				))
				
				conn.commit()
				
		except Exception as e:
			self.logger.error(f"Error storing bond signal: {e}")
	
	def store_chip_signal(self, signal: ChipTradingSignal):
		"""Store chip trading signal in database"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cursor.execute("""
					INSERT INTO chip_trading_signals 
					(timestamp, symbol, signal_type, signal_strength, confidence_score,
					 target_horizon_days, bond_correlation, suggested_position_size,
					 entry_price, stop_loss, take_profit, reasoning)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""", (
					signal.timestamp,
					signal.symbol,
					signal.signal_type,
					signal.signal_strength.value,
					signal.confidence_score,
					signal.target_horizon_days,
					signal.bond_correlation,
					signal.suggested_position_size,
					signal.entry_price,
					signal.stop_loss,
					signal.take_profit,
					signal.reasoning
				))
				
				conn.commit()
				
		except Exception as e:
			self.logger.error(f"Error storing chip signal: {e}")
	
	def get_latest_bond_signal(self) -> Optional[Dict]:
		"""Get the most recent bond stress signal"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cursor.execute("""
					SELECT * FROM bond_stress_signals 
					ORDER BY timestamp DESC 
					LIMIT 1
				""")
				
				result = cursor.fetchone()
				
				if result:
					columns = [description[0] for description in cursor.description]
					return dict(zip(columns, result))
				
				return None
				
		except Exception as e:
			self.logger.error(f"Error fetching latest bond signal: {e}")
			return None
	
	def get_latest_chip_signals(self, limit: int = 10) -> List[Dict]:
		"""Get the most recent chip trading signals"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cursor.execute("""
					SELECT * FROM chip_trading_signals 
					ORDER BY timestamp DESC 
					LIMIT ?
				""", (limit,))
				
				results = cursor.fetchall()
				columns = [description[0] for description in cursor.description]
				
				return [dict(zip(columns, row)) for row in results]
				
		except Exception as e:
			self.logger.error(f"Error fetching chip signals: {e}")
			return []
	
	def get_historical_signals(self, symbol: str = None, days: int = 30) -> List[Dict]:
		"""Get historical signals for analysis"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				end_date = datetime.now()
				start_date = end_date - timedelta(days=days)
				
				if symbol:
					cursor.execute("""
						SELECT * FROM chip_trading_signals 
						WHERE symbol = ? AND timestamp >= ?
						ORDER BY timestamp DESC
					""", (symbol, start_date))
				else:
					cursor.execute("""
						SELECT * FROM chip_trading_signals 
						WHERE timestamp >= ?
						ORDER BY timestamp DESC
					""", (start_date,))
				
				results = cursor.fetchall()
				columns = [description[0] for description in cursor.description]
				
				return [dict(zip(columns, row)) for row in results]
				
		except Exception as e:
			self.logger.error(f"Error fetching historical signals: {e}")
			return []
	
	def cache_market_data(self, data_type: str, data: Dict, symbol: str = None):
		"""Cache market data for faster retrieval"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cursor.execute("""
					INSERT INTO market_data_cache (data_type, symbol, timestamp, data_json)
					VALUES (?, ?, ?, ?)
				""", (
					data_type,
					symbol,
					datetime.now(),
					json.dumps(data, default=str)
				))
				
				conn.commit()
				
				# Clean old cache entries (keep last 7 days)
				cutoff_date = datetime.now() - timedelta(days=7)
				cursor.execute("""
					DELETE FROM market_data_cache 
					WHERE created_at < ?
				""", (cutoff_date,))
				
				conn.commit()
				
		except Exception as e:
			self.logger.error(f"Error caching market data: {e}")
	
	def get_cached_data(self, data_type: str, symbol: str = None, max_age_minutes: int = 30) -> Optional[Dict]:
		"""Retrieve cached market data if still fresh"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
				
				if symbol:
					cursor.execute("""
						SELECT data_json FROM market_data_cache 
						WHERE data_type = ? AND symbol = ? AND created_at >= ?
						ORDER BY created_at DESC 
						LIMIT 1
					""", (data_type, symbol, cutoff_time))
				else:
					cursor.execute("""
						SELECT data_json FROM market_data_cache 
						WHERE data_type = ? AND created_at >= ?
						ORDER BY created_at DESC 
						LIMIT 1
					""", (data_type, cutoff_time))
				
				result = cursor.fetchone()
				
				if result:
					return json.loads(result[0])
				
				return None
				
		except Exception as e:
			self.logger.error(f"Error retrieving cached data: {e}")
			return None
	
	def record_signal_performance(self, signal_id: int, symbol: str, entry_price: float, 
								  exit_price: float, entry_date: datetime, exit_date: datetime):
		"""Record the performance of a trading signal"""
		try:
			holding_days = (exit_date - entry_date).days
			return_pct = (exit_price - entry_price) / entry_price * 100
			
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cursor.execute("""
					INSERT INTO signal_performance 
					(signal_id, symbol, entry_date, exit_date, entry_price, exit_price, 
					 return_pct, holding_days)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?)
				""", (
					signal_id, symbol, entry_date, exit_date,
					entry_price, exit_price, return_pct, holding_days
				))
				
				conn.commit()
				
		except Exception as e:
			self.logger.error(f"Error recording signal performance: {e}")
	
	def get_performance_stats(self, days: int = 90) -> Dict:
		"""Get trading signal performance statistics"""
		try:
			with sqlite3.connect(self.db_path) as conn:
				cursor = conn.cursor()
				
				cutoff_date = datetime.now() - timedelta(days=days)
				
				cursor.execute("""
					SELECT 
						COUNT(*) as total_signals,
						AVG(return_pct) as avg_return,
						COUNT(CASE WHEN return_pct > 0 THEN 1 END) as winning_trades,
						MAX(return_pct) as best_return,
						MIN(return_pct) as worst_return,
						AVG(holding_days) as avg_holding_days
					FROM signal_performance 
					WHERE entry_date >= ?
				""", (cutoff_date,))
				
				result = cursor.fetchone()
				columns = [description[0] for description in cursor.description]
				stats = dict(zip(columns, result))
				
				# Calculate win rate
				if stats['total_signals'] > 0:
					stats['win_rate'] = stats['winning_trades'] / stats['total_signals'] * 100
				else:
					stats['win_rate'] = 0
				
				return stats
				
		except Exception as e:
			self.logger.error(f"Error getting performance stats: {e}")
			return {}
