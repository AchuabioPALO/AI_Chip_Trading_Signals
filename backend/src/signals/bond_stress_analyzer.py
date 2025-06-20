import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class SignalStrength(Enum):
	"""Signal strength classification"""
	NOW = "NOW"
	SOON = "SOON" 
	WATCH = "WATCH"
	NEUTRAL = "NEUTRAL"

@dataclass
class BondStressSignal:
	"""Bond stress signal data structure"""
	timestamp: datetime
	yield_curve_spread: float
	yield_curve_zscore: float
	bond_volatility: float
	credit_spreads: float
	signal_strength: SignalStrength
	confidence_score: float  # 1-10 scale
	suggested_action: str
	
class BondStressAnalyzer:
	"""Analyzes bond market stress indicators for trading signals"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		
	def calculate_yield_curve_spread(self, ten_year_yields: pd.Series, two_year_yields: pd.Series) -> pd.Series:
		"""Calculate 10Y-2Y yield curve spread"""
		try:
			# Align the series by date
			aligned_data = pd.DataFrame({
				'10Y': ten_year_yields,
				'2Y': two_year_yields
			}).dropna()
			
			spread = aligned_data['10Y'] - aligned_data['2Y']
			return spread
		except Exception as e:
			self.logger.error(f"Error calculating yield curve spread: {e}")
			return pd.Series()
	
	def calculate_rolling_zscore(self, data: pd.Series, window: int = 20) -> pd.Series:
		"""Calculate rolling z-score for anomaly detection"""
		try:
			rolling_mean = data.rolling(window=window).mean()
			rolling_std = data.rolling(window=window).std()
			
			zscore = (data - rolling_mean) / rolling_std
			return zscore.fillna(0)
		except Exception as e:
			self.logger.error(f"Error calculating z-score: {e}")
			return pd.Series()
	
	def calculate_bond_volatility(self, bond_prices: Dict[str, pd.DataFrame], window: int = 20) -> pd.Series:
		"""Calculate bond market volatility using TLT returns"""
		try:
			if 'TLT' not in bond_prices or bond_prices['TLT'].empty:
				self.logger.warning("TLT data not available for volatility calculation")
				return pd.Series()
			
			tlt_prices = bond_prices['TLT']['Close']
			returns = tlt_prices.pct_change().dropna()
			volatility = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
			
			return volatility
		except Exception as e:
			self.logger.error(f"Error calculating bond volatility: {e}")
			return pd.Series()
	
	def calculate_credit_spreads(self, bond_data: Dict[str, pd.DataFrame]) -> pd.Series:
		"""Calculate credit spreads using HYG vs LQD"""
		try:
			if 'HYG' not in bond_data or 'LQD' not in bond_data:
				self.logger.warning("Credit spread data not available")
				return pd.Series()
			
			# Calculate yields proxy using inverse of price changes
			hyg_returns = bond_data['HYG']['Close'].pct_change()
			lqd_returns = bond_data['LQD']['Close'].pct_change()
			
			# Credit spread proxy (high yield underperformance vs investment grade)
			credit_spread = lqd_returns - hyg_returns
			return credit_spread
		except Exception as e:
			self.logger.error(f"Error calculating credit spreads: {e}")
			return pd.Series()
	
	def generate_stress_signal(self, 
		yield_curve_spread: pd.Series,
		bond_volatility: pd.Series,
		credit_spreads: pd.Series,
		lookback_short: int = 20,
		lookback_long: int = 60
	) -> BondStressSignal:
		"""Generate comprehensive bond stress signal"""
		
		try:
			latest_date = max(
				yield_curve_spread.index[-1] if not yield_curve_spread.empty else datetime.min,
				bond_volatility.index[-1] if not bond_volatility.empty else datetime.min,
				credit_spreads.index[-1] if not credit_spreads.empty else datetime.min
			)
			
			# Get latest values
			current_spread = yield_curve_spread.iloc[-1] if not yield_curve_spread.empty else 0
			current_volatility = bond_volatility.iloc[-1] if not bond_volatility.empty else 0
			current_credit_spread = credit_spreads.iloc[-1] if not credit_spreads.empty else 0
			
			# Calculate z-scores
			spread_zscore_short = self.calculate_rolling_zscore(yield_curve_spread, lookback_short).iloc[-1] if not yield_curve_spread.empty else 0
			spread_zscore_long = self.calculate_rolling_zscore(yield_curve_spread, lookback_long).iloc[-1] if not yield_curve_spread.empty else 0
			
			volatility_zscore = self.calculate_rolling_zscore(bond_volatility, lookback_short).iloc[-1] if not bond_volatility.empty else 0
			credit_zscore = self.calculate_rolling_zscore(credit_spreads, lookback_short).iloc[-1] if not credit_spreads.empty else 0
			
			# Signal logic based on z-score thresholds
			signal_strength, confidence, action = self._classify_stress_signal(
				spread_zscore_short, spread_zscore_long, volatility_zscore, credit_zscore
			)
			
			return BondStressSignal(
				timestamp=latest_date,
				yield_curve_spread=current_spread,
				yield_curve_zscore=spread_zscore_short,
				bond_volatility=current_volatility,
				credit_spreads=current_credit_spread,
				signal_strength=signal_strength,
				confidence_score=confidence,
				suggested_action=action
			)
			
		except Exception as e:
			self.logger.error(f"Error generating stress signal: {e}")
			return BondStressSignal(
				timestamp=datetime.now(),
				yield_curve_spread=0,
				yield_curve_zscore=0,
				bond_volatility=0,
				credit_spreads=0,
				signal_strength=SignalStrength.NEUTRAL,
				confidence_score=0,
				suggested_action="Data unavailable"
			)
	
	def _classify_stress_signal(self, 
		spread_zscore_short: float, 
		spread_zscore_long: float, 
		volatility_zscore: float, 
		credit_zscore: float
	) -> Tuple[SignalStrength, float, str]:
		"""Classify stress signal based on z-score thresholds"""
		
		# Stress indicators: negative yield curve z-score, high volatility, widening credit spreads
		stress_score = 0
		confidence_factors = []
		
		# Yield curve inversion signal (negative z-score = flattening/inversion)
		if spread_zscore_short < -2.0:
			stress_score += 3
			confidence_factors.append("Strong yield curve inversion")
		elif spread_zscore_short < -1.5:
			stress_score += 2
			confidence_factors.append("Moderate yield curve flattening")
		elif spread_zscore_short < -1.0:
			stress_score += 1
			confidence_factors.append("Mild yield curve flattening")
		
		# Volatility spike signal
		if volatility_zscore > 2.0:
			stress_score += 3
			confidence_factors.append("High bond volatility spike")
		elif volatility_zscore > 1.5:
			stress_score += 2
			confidence_factors.append("Elevated bond volatility")
		elif volatility_zscore > 1.0:
			stress_score += 1
			confidence_factors.append("Rising bond volatility")
		
		# Credit spread widening
		if credit_zscore > 2.0:
			stress_score += 3
			confidence_factors.append("Significant credit spread widening")
		elif credit_zscore > 1.5:
			stress_score += 2
			confidence_factors.append("Moderate credit stress")
		elif credit_zscore > 1.0:
			stress_score += 1
			confidence_factors.append("Minor credit spread widening")
		
		# Long-term trend confirmation
		if spread_zscore_long < -1.0 and spread_zscore_short < spread_zscore_long:
			stress_score += 1
			confidence_factors.append("Sustained yield curve trend")
		
		# Signal classification
		if stress_score >= 7:
			signal = SignalStrength.NOW
			action = f"TRADE NOW - High stress detected: {', '.join(confidence_factors[:2])}"
			confidence = min(10.0, stress_score + 1)
		elif stress_score >= 4:
			signal = SignalStrength.SOON
			action = f"PREPARE TO TRADE - Moderate stress: {', '.join(confidence_factors[:2])}"
			confidence = min(8.0, stress_score)
		elif stress_score >= 2:
			signal = SignalStrength.WATCH
			action = f"MONITOR CLOSELY - Early stress signals: {', '.join(confidence_factors[:1])}"
			confidence = min(6.0, stress_score)
		else:
			signal = SignalStrength.NEUTRAL
			action = "No significant stress detected"
			confidence = max(1.0, stress_score)
		
		return signal, confidence, action
