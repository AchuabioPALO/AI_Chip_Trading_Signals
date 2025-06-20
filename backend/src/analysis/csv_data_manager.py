"""
CSV Data Manager for Historical Analysis
Simple file-based storage for backtesting and signal tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from typing import Dict, List, Any, Optional
import glob

class CSVDataManager:
	"""Simple CSV-based data management for historical analysis"""
	
	def __init__(self, data_dir: str = "../data/analysis_results"):
		self.logger = logging.getLogger(__name__)
		self.data_dir = data_dir
		self.ensure_directories()
		
	def ensure_directories(self):
		"""Create necessary directories for CSV storage"""
		directories = [
			self.data_dir,
			f"{self.data_dir}/signals",
			f"{self.data_dir}/prices", 
			f"{self.data_dir}/backtests",
			f"{self.data_dir}/performance"
		]
		
		for directory in directories:
			os.makedirs(directory, exist_ok=True)
			
	def export_historical_signals(self, signals_data: List[Dict]) -> str:
		"""Export signal data to CSV for analysis"""
		if not signals_data:
			self.logger.warning("No signals data to export")
			return None
			
		df = pd.DataFrame(signals_data)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"{self.data_dir}/signals/historical_signals_{timestamp}.csv"
		
		df.to_csv(filename, index=False)
		self.logger.info(f"Exported {len(df)} signals to {filename}")
		return filename
		
	def export_price_data(self, symbol: str, price_data: pd.DataFrame) -> str:
		"""Export price data for a symbol"""
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"{self.data_dir}/prices/{symbol}_prices_{timestamp}.csv"
		
		price_data.to_csv(filename)
		self.logger.info(f"Exported {symbol} price data to {filename}")
		return filename
		
	def load_latest_signals(self) -> Optional[pd.DataFrame]:
		"""Load the most recent signals CSV file"""
		pattern = f"{self.data_dir}/signals/historical_signals_*.csv"
		files = glob.glob(pattern)
		
		if not files:
			self.logger.warning("No historical signals files found")
			return None
			
		latest_file = max(files, key=os.path.getctime)
		self.logger.info(f"Loading signals from {latest_file}")
		return pd.read_csv(latest_file)
		
	def save_backtest_results(self, results: Dict[str, Any], test_name: str) -> str:
		"""Save backtest results to CSV"""
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"{self.data_dir}/backtests/{test_name}_{timestamp}.csv"
		
		# Convert results dict to DataFrame
		if 'portfolio_values' in results:
			portfolio_df = pd.DataFrame(results['portfolio_values'])
			portfolio_df.to_csv(filename.replace('.csv', '_portfolio.csv'))
			
		# Save summary metrics
		summary_data = {k: [v] for k, v in results.items() if not isinstance(v, (list, dict, pd.DataFrame))}
		summary_df = pd.DataFrame(summary_data)
		summary_df.to_csv(filename.replace('.csv', '_summary.csv'), index=False)
		
		self.logger.info(f"Saved backtest results to {filename}")
		return filename
		
	def create_sample_historical_data(self) -> Dict[str, str]:
		"""Create sample historical data for testing"""
		# Generate sample signals
		dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
		symbols = ['NVDA', 'AMD', 'TSM', 'INTC', 'QCOM']
		
		signals = []
		for date in dates:
			for symbol in np.random.choice(symbols, size=np.random.randint(0, 3), replace=False):
				signal = {
					'timestamp': date,
					'symbol': symbol,
					'signal_type': np.random.choice(['NOW', 'SOON', 'WATCH']),
					'signal_strength': np.random.choice(['STRONG', 'MODERATE', 'WEAK']),
					'confidence_score': np.random.uniform(3.0, 9.5),
					'target_horizon_days': np.random.randint(5, 60),
					'bond_correlation': np.random.uniform(-0.8, 0.8),
					'suggested_position_size': np.random.uniform(0.02, 0.15),
					'entry_price': np.random.uniform(50, 200),
					'reasoning': f"Sample signal for {symbol} on {date.strftime('%Y-%m-%d')}"
				}
				signals.append(signal)
				
		signals_file = self.export_historical_signals(signals)
		
		# Generate sample price data
		price_files = {}
		for symbol in symbols:
			dates_extended = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
			price_data = pd.DataFrame({
				'Date': dates_extended,
				'Open': np.random.uniform(50, 200, len(dates_extended)),
				'High': np.random.uniform(55, 210, len(dates_extended)),
				'Low': np.random.uniform(45, 190, len(dates_extended)),
				'Close': np.random.uniform(50, 200, len(dates_extended)),
				'Volume': np.random.randint(1000000, 50000000, len(dates_extended))
			})
			# Add realistic price walk
			price_data['Close'] = price_data['Close'].iloc[0] + np.cumsum(np.random.normal(0, 2, len(dates_extended)))
			price_data['Close'] = np.maximum(price_data['Close'], 10)  # Minimum price
			
			price_files[symbol] = self.export_price_data(symbol, price_data)
			
		self.logger.info("Created sample historical data for analysis")
		return {'signals': signals_file, 'prices': price_files}
		
	def get_available_data_files(self) -> Dict[str, List[str]]:
		"""Get list of available data files"""
		return {
			'signals': glob.glob(f"{self.data_dir}/signals/*.csv"),
			'prices': glob.glob(f"{self.data_dir}/prices/*.csv"),
			'backtests': glob.glob(f"{self.data_dir}/backtests/*.csv"),
			'performance': glob.glob(f"{self.data_dir}/performance/*.csv")
		}
