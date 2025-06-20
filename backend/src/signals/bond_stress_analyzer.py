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
		"""Calculate rolling z-score for anomaly detection using REAL historical data"""
		try:
			if len(data) < 10:  # Need minimum 10 data points for meaningful z-score
				self.logger.error(f"INSUFFICIENT DATA for real z-score calculation: {len(data)} points (need ≥10)")
				# Return NaN instead of fake data
				return pd.Series([np.nan] * len(data), index=data.index)
			
			# Use actual historical window - no compromises
			if len(data) < window:
				self.logger.warning(f"Using shorter window: {len(data)} vs requested {window}")
				effective_window = len(data)
			else:
				effective_window = window
			
			# Calculate proper rolling statistics
			rolling_mean = data.rolling(window=effective_window, min_periods=effective_window//2).mean()
			rolling_std = data.rolling(window=effective_window, min_periods=effective_window//2).std()
			
			# Only calculate z-score where we have sufficient data
			mask = rolling_std > 0.001  # Avoid division by near-zero
			zscore = pd.Series(np.nan, index=data.index)
			zscore[mask] = (data[mask] - rolling_mean[mask]) / rolling_std[mask]
			
			# Log actual calculation details
			if not zscore.isna().all():
				latest_zscore = zscore.iloc[-1]
				self.logger.info(f"Real z-score calculated: {latest_zscore:.3f} from {len(data)} data points")
			else:
				self.logger.error("Z-score calculation failed - returning NaN (no fake data)")
			
			return zscore
		except Exception as e:
			self.logger.error(f"Error calculating real z-score: {e}")
			# Return NaN series instead of fake zeros
			return pd.Series([np.nan] * len(data), index=data.index)
	
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
			
			# Calculate z-scores - ONLY use real historical data
			spread_zscore_short = np.nan
			spread_zscore_long = np.nan
			volatility_zscore = np.nan
			credit_zscore = np.nan
			
			if not yield_curve_spread.empty and len(yield_curve_spread) >= 10:
				zscore_series_short = self.calculate_rolling_zscore(yield_curve_spread, lookback_short)
				zscore_series_long = self.calculate_rolling_zscore(yield_curve_spread, lookback_long)
				if not zscore_series_short.isna().all():
					spread_zscore_short = zscore_series_short.iloc[-1]
				if not zscore_series_long.isna().all():
					spread_zscore_long = zscore_series_long.iloc[-1]
				self.logger.info(f"Spread z-scores: short={spread_zscore_short:.3f}, long={spread_zscore_long:.3f}")
			else:
				self.logger.error(f"Insufficient yield curve data: {len(yield_curve_spread)} points")
			
			if not bond_volatility.empty and len(bond_volatility) >= 10:
				zscore_series = self.calculate_rolling_zscore(bond_volatility, lookback_short)
				if not zscore_series.isna().all():
					volatility_zscore = zscore_series.iloc[-1]
				self.logger.info(f"Volatility z-score: {volatility_zscore:.3f}")
			else:
				self.logger.error(f"Insufficient volatility data: {len(bond_volatility)} points")
			
			if not credit_spreads.empty and len(credit_spreads) >= 10:
				zscore_series = self.calculate_rolling_zscore(credit_spreads, lookback_short)
				if not zscore_series.isna().all():
					credit_zscore = zscore_series.iloc[-1]
				self.logger.info(f"Credit z-score: {credit_zscore:.3f}")
			else:
				self.logger.error(f"Insufficient credit data: {len(credit_spreads)} points")
			
			# Signal logic based on z-score thresholds
			signal_strength, confidence, action = self._classify_stress_signal(
				spread_zscore_short, spread_zscore_long, volatility_zscore, credit_zscore
			)
			
			return BondStressSignal(
				timestamp=latest_date,
				yield_curve_spread=current_spread,
				yield_curve_zscore=spread_zscore_short if not np.isnan(spread_zscore_short) else 0.0,
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
		"""Classify stress signal based on z-score thresholds - REQUIRES REAL DATA"""
		
		# Check if we have real data (not NaN)
		valid_scores = []
		if not np.isnan(spread_zscore_short):
			valid_scores.append(f"Yield curve z-score: {spread_zscore_short:.2f}")
		if not np.isnan(volatility_zscore):
			valid_scores.append(f"Volatility z-score: {volatility_zscore:.2f}")
		if not np.isnan(credit_zscore):
			valid_scores.append(f"Credit z-score: {credit_zscore:.2f}")
		
		# If we don't have enough real data, return low confidence signal
		if len(valid_scores) == 0:
			return (
				SignalStrength.NEUTRAL, 
				0.5, 
				"INSUFFICIENT HISTORICAL DATA - Need 10+ days for real z-scores"
			)
		
		# Only calculate stress from REAL z-scores
		stress_score = 0
		confidence_factors = []
		
		# Yield curve signals (only if we have real data)
		if not np.isnan(spread_zscore_short):
			if spread_zscore_short < -2.0:
				stress_score += 3
				confidence_factors.append(f"Strong yield curve inversion ({spread_zscore_short:.2f}σ)")
			elif spread_zscore_short < -1.5:
				stress_score += 2
				confidence_factors.append(f"Moderate yield curve flattening ({spread_zscore_short:.2f}σ)")
			elif spread_zscore_short < -1.0:
				stress_score += 1
				confidence_factors.append(f"Mild yield curve flattening ({spread_zscore_short:.2f}σ)")
		
		# Volatility signals (only if we have real data)
		if not np.isnan(volatility_zscore):
			if volatility_zscore > 2.0:
				stress_score += 3
				confidence_factors.append(f"High bond volatility spike ({volatility_zscore:.2f}σ)")
			elif volatility_zscore > 1.5:
				stress_score += 2
				confidence_factors.append(f"Elevated bond volatility ({volatility_zscore:.2f}σ)")
			elif volatility_zscore > 1.0:
				stress_score += 1
				confidence_factors.append(f"Rising bond volatility ({volatility_zscore:.2f}σ)")
		
		# Credit signals (only if we have real data)
		if not np.isnan(credit_zscore):
			if credit_zscore > 2.0:
				stress_score += 3
				confidence_factors.append(f"Significant credit spread widening ({credit_zscore:.2f}σ)")
			elif credit_zscore > 1.5:
				stress_score += 2
				confidence_factors.append(f"Moderate credit stress ({credit_zscore:.2f}σ)")
			elif credit_zscore > 1.0:
				stress_score += 1
				confidence_factors.append(f"Minor credit spread widening ({credit_zscore:.2f}σ)")
		
		# Long-term trend (only if we have real data)
		if not np.isnan(spread_zscore_long) and not np.isnan(spread_zscore_short):
			if spread_zscore_long < -1.0 and spread_zscore_short < spread_zscore_long:
				stress_score += 1
				confidence_factors.append("Sustained yield curve trend")
		
		# Signal classification based on REAL data
		data_quality = f"Real data: {', '.join(valid_scores)}"
		
		if stress_score >= 7:
			signal = SignalStrength.NOW
			action = f"TRADE NOW - {'; '.join(confidence_factors[:2])} | {data_quality}"
			confidence = min(10.0, stress_score + len(valid_scores))
		elif stress_score >= 4:
			signal = SignalStrength.SOON
			action = f"PREPARE TO TRADE - {'; '.join(confidence_factors[:2])} | {data_quality}"
			confidence = min(8.0, stress_score + len(valid_scores))
		elif stress_score >= 2:
			signal = SignalStrength.WATCH
			action = f"MONITOR CLOSELY - {'; '.join(confidence_factors[:1])} | {data_quality}"
			confidence = min(6.0, stress_score + len(valid_scores))
		else:
			signal = SignalStrength.NEUTRAL
			action = f"No significant stress detected | {data_quality}"
			confidence = max(1.0, len(valid_scores))
		
		return signal, confidence, action
