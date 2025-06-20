import yfinance as yf
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

class YahooFinanceClient:
	"""Yahoo Finance client for bond ETF and AI chip stock data"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		
	def get_bond_etf_data(self, symbols: List[str] = None, period: str = "1y") -> Dict[str, pd.DataFrame]:
		"""Fetch bond ETF data for stress monitoring"""
		if symbols is None:
			symbols = ['TLT', 'IEF', 'SHY', 'HYG', 'LQD']  # Long, intermediate, short, high yield, investment grade
			
		bond_data = {}
		
		for symbol in symbols:
			try:
				ticker = yf.Ticker(symbol)
				hist = ticker.history(period=period)
				
				if not hist.empty:
					# Ensure timezone-naive data to match FRED
					if hist.index.tz is not None:
						hist.index = hist.index.tz_convert('UTC').tz_localize(None)
					bond_data[symbol] = hist[['Close', 'Volume']]
					self.logger.info(f"Fetched {len(hist)} days of data for {symbol}")
				else:
					self.logger.warning(f"No data returned for {symbol}")
					
				time.sleep(0.1)  # Rate limiting
					
			except Exception as e:
				self.logger.error(f"Error fetching {symbol}: {e}")
				
		return bond_data
	
	def get_ai_chip_stocks(self, symbols: List[str] = None, period: str = "1y") -> Dict[str, pd.DataFrame]:
		"""Fetch AI chip stock data"""
		if symbols is None:
			symbols = ['NVDA', 'AMD', 'TSM', 'INTC', 'QCOM']
			
		stock_data = {}
		
		for symbol in symbols:
			try:
				ticker = yf.Ticker(symbol)
				hist = ticker.history(period=period)
				
				if not hist.empty:
					# Ensure timezone-naive data to match FRED
					if hist.index.tz is not None:
						hist.index = hist.index.tz_convert('UTC').tz_localize(None)
					stock_data[symbol] = hist[['Close', 'Volume']]
					self.logger.info(f"Fetched {len(hist)} days of data for {symbol}")
				
				time.sleep(0.1)  # Rate limiting
					
			except Exception as e:
				self.logger.error(f"Error fetching {symbol}: {e}")
				
		return stock_data
	
	def get_vix_data(self, period: str = "1y") -> pd.DataFrame:
		"""Fetch VIX volatility index"""
		try:
			vix = yf.Ticker("^VIX")
			hist = vix.history(period=period)
			# Ensure timezone-naive data
			if not hist.empty and hist.index.tz is not None:
				hist.index = hist.index.tz_convert('UTC').tz_localize(None)
			return hist[['Close']]
		except Exception as e:
			self.logger.error(f"Error fetching VIX: {e}")
			return pd.DataFrame()
	
	def get_move_index_proxy(self, period: str = "1y") -> pd.DataFrame:
		"""Get MOVE index proxy using bond volatility ETF"""
		try:
			# Using VIXM (1 month VIX futures) as MOVE proxy since MOVE isn't directly available
			move_proxy = yf.Ticker("VIXM")
			hist = move_proxy.history(period=period)
			# Ensure timezone-naive data
			if not hist.empty and hist.index.tz is not None:
				hist.index = hist.index.tz_convert('UTC').tz_localize(None)
			return hist[['Close']]
		except Exception as e:
			self.logger.error(f"Error fetching MOVE proxy: {e}")
			return pd.DataFrame()
	
	def get_real_time_quote(self, symbol: str) -> Optional[Dict]:
		"""Get real-time quote for a symbol"""
		try:
			ticker = yf.Ticker(symbol)
			info = ticker.info
			
			return {
				'symbol': symbol,
				'price': info.get('currentPrice', info.get('regularMarketPrice')),
				'change': info.get('regularMarketChange'),
				'change_percent': info.get('regularMarketChangePercent'),
				'volume': info.get('regularMarketVolume'),
				'timestamp': datetime.now()
			}
		except Exception as e:
			self.logger.error(f"Error fetching real-time quote for {symbol}: {e}")
			return None
