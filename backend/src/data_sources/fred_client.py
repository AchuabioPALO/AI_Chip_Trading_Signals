import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time
import os
from dotenv import load_dotenv

load_dotenv()

class FredClient:
	"""Federal Reserve Economic Data API client for treasury yield data"""
	
	def __init__(self, api_key: str = None):
		self.api_key = api_key or os.getenv('FRED_API_KEY')
		self.base_url = "https://api.stlouisfed.org/fred/series/observations"
		self.logger = logging.getLogger(__name__)
		
		if not self.api_key:
			self.logger.warning("No FRED API key provided. Get one free at https://fred.stlouisfed.org/docs/api/api_key.html")
		
	def get_treasury_yields(self, series_id: str, days_back: int = 500) -> pd.DataFrame:
		"""Fetch treasury yield data from FRED API"""
		if not self.api_key or self.api_key == "demo_key":
			self.logger.warning(f"Using mock data for {series_id} - no valid FRED API key")
			return self._get_mock_yield_data(series_id, days_back)
			
		try:
			end_date = datetime.now()
			start_date = end_date - timedelta(days=days_back)
			
			params = {
				'series_id': series_id,
				'api_key': self.api_key,
				'file_type': 'json',
				'observation_start': start_date.strftime('%Y-%m-%d'),
				'observation_end': end_date.strftime('%Y-%m-%d')
			}
			
			response = requests.get(self.base_url, params=params, timeout=10)
			response.raise_for_status()
			
			data = response.json()
			observations = data['observations']
			
			df = pd.DataFrame(observations)
			df['date'] = pd.to_datetime(df['date'])
			df['value'] = pd.to_numeric(df['value'], errors='coerce')
			df = df.dropna()
			
			# Convert to timezone-naive to match Yahoo Finance data
			df = df.set_index('date')
			if df.index.tz is not None:
				df.index = df.index.tz_convert('UTC').tz_localize(None)
			
			self.logger.info(f"Fetched {len(df)} observations for {series_id}")
			return df[['value']]
			
		except Exception as e:
			self.logger.error(f"Error fetching {series_id}: {e}")
			return pd.DataFrame()
	
	def get_yield_curve_data(self) -> Dict[str, pd.DataFrame]:
		"""Get 2Y and 10Y treasury yields for spread calculation"""
		series_map = {
			'2Y': 'GS2',
			'10Y': 'GS10'
		}
		
		yield_data = {}
		for name, series_id in series_map.items():
			yield_data[name] = self.get_treasury_yields(series_id)
			time.sleep(0.2)  # Rate limiting - FRED allows 120 calls/minute
			
		return yield_data
	
	def calculate_yield_spread(self, yield_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
		"""Calculate 10Y-2Y yield spread"""
		try:
			if '10Y' in yield_data and '2Y' in yield_data:
				spread_df = yield_data['10Y'].join(yield_data['2Y'], rsuffix='_2Y')
				spread_df['spread'] = spread_df['value'] - spread_df['value_2Y']
				return spread_df[['spread']].dropna()
			else:
				self.logger.error("Missing yield data for spread calculation")
				return pd.DataFrame()
				
		except Exception as e:
			self.logger.error(f"Error calculating yield spread: {e}")
			return pd.DataFrame()
	
	def _get_mock_yield_data(self, series_id: str, days_back: int) -> pd.DataFrame:
		"""Generate mock yield data for demo purposes"""
		import numpy as np
		
		# Create date range
		end_date = datetime.now()
		start_date = end_date - timedelta(days=days_back)
		dates = pd.date_range(start=start_date, end=end_date, freq='D')
		
		# Mock yield levels based on series
		if series_id == 'GS2':  # 2-Year Treasury
			base_yield = 4.5
		elif series_id == 'GS10':  # 10-Year Treasury
			base_yield = 4.8
		else:
			base_yield = 4.0
			
		# Generate realistic yield data with some volatility
		np.random.seed(42)  # For reproducible demo data
		yields = base_yield + np.cumsum(np.random.normal(0, 0.02, len(dates)))
		
		# Create DataFrame matching FRED format
		mock_data = pd.DataFrame({
			'date': dates,
			'value': yields
		})
		mock_data['date'] = pd.to_datetime(mock_data['date'])
		mock_data = mock_data.set_index('date')
		
		# Ensure timezone-naive to match real FRED data processing
		if mock_data.index.tz is not None:
			mock_data.index = mock_data.index.tz_convert('UTC').tz_localize(None)
		
		self.logger.info(f"Generated {len(mock_data)} days of mock data for {series_id}")
		return mock_data
