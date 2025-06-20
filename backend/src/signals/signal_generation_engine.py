#!/usr/bin/env python3
"""
Enhanced Signal Generation Engine
Implements Feature 02 requirements autonomously
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
import os

class SignalGenerationEngine:
	"""Enhanced signal generation with ML and multi-timeframe analysis"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.scaler = StandardScaler()
		self.linear_model = LinearRegression()
		self.is_trained = False
		
		# Signal thresholds (Feature 02 requirement)
		self.signal_thresholds = {
			'NOW': 8.0,      # High confidence signals
			'SOON': 6.0,     # Medium confidence signals  
			'WATCH': 4.0,    # Low confidence signals
			'NEUTRAL': 0.0   # No signal
		}
		
		# VIX-based position sizing (Feature 02 requirement)
		self.vix_sizing = {
			'low': {'vix_max': 20, 'position_size': 0.02},    # 2% when VIX < 20
			'medium': {'vix_max': 30, 'position_size': 0.015}, # 1.5% when VIX 20-30
			'high': {'vix_max': 100, 'position_size': 0.005}   # 0.5% when VIX > 30
		}
		
		# Hard limits (Feature 02 requirement)
		self.max_position_size = 0.03  # 3% max per position
		self.max_total_exposure = 0.20  # 20% max total exposure
		
		# Multi-timeframe windows (Feature 02 requirement)
		self.timeframes = {
			'short': 20,   # 20-day analysis
			'medium': 40,  # 40-day analysis  
			'long': 60     # 60-day analysis
		}
		
	def prepare_features_multi_timeframe(self, bond_data: pd.DataFrame, 
		chip_data: pd.DataFrame, vix_data: pd.DataFrame) -> pd.DataFrame:
		"""Prepare multi-timeframe features for signal generation"""
		
		try:
			features = pd.DataFrame(index=bond_data.index)
			
			# Bond stress features across multiple timeframes
			for name, window in self.timeframes.items():
				# Yield curve features
				features[f'yield_spread_{name}'] = bond_data.get('yield_spread', pd.Series())
				features[f'yield_zscore_{name}'] = self._calculate_zscore(
					bond_data.get('yield_spread', pd.Series()), window
				)
				
				# Bond volatility features
				features[f'bond_vol_{name}'] = bond_data.get('bond_volatility', pd.Series())
				features[f'bond_vol_zscore_{name}'] = self._calculate_zscore(
					bond_data.get('bond_volatility', pd.Series()), window
				)
				
				# Credit spread features
				features[f'credit_spread_{name}'] = bond_data.get('credit_spreads', pd.Series())
				features[f'credit_zscore_{name}'] = self._calculate_zscore(
					bond_data.get('credit_spreads', pd.Series()), window
				)
			
			# VIX regime detection (Feature 02 requirement)
			if not vix_data.empty:
				features['vix'] = vix_data
				features['vix_regime'] = self._detect_vix_regime(vix_data)
				features['vix_zscore'] = self._calculate_zscore(vix_data, 20)
			
			# Chip momentum features
			if not chip_data.empty:
				for name, window in self.timeframes.items():
					features[f'chip_momentum_{name}'] = chip_data.pct_change(window)
					features[f'chip_volatility_{name}'] = chip_data.rolling(window).std()
			
			# Interaction features
			features['stress_composite'] = (
				features.get('yield_zscore_short', 0) * -1 +  # Inversion = stress
				features.get('bond_vol_zscore_short', 0) +
				features.get('credit_zscore_short', 0)
			) / 3
			
			# Drop NaN values
			features = features.fillna(method='ffill').fillna(0)
			
			self.logger.info(f"Prepared multi-timeframe features: {features.shape}")
			return features
			
		except Exception as e:
			self.logger.error(f"Error preparing multi-timeframe features: {e}")
			return pd.DataFrame()
	
	def _calculate_zscore(self, data: pd.Series, window: int) -> pd.Series:
		"""Calculate rolling z-score for given window"""
		rolling_mean = data.rolling(window).mean()
		rolling_std = data.rolling(window).std()
		return (data - rolling_mean) / rolling_std
	
	def _detect_vix_regime(self, vix_data: pd.Series) -> pd.Series:
		"""Detect VIX-based market regime (Feature 02 requirement)"""
		regimes = pd.Series(index=vix_data.index, dtype='category')
		
		regimes[vix_data < 20] = 'low_vol'     # Low volatility regime
		regimes[(vix_data >= 20) & (vix_data < 30)] = 'medium_vol'  # Medium volatility
		regimes[vix_data >= 30] = 'high_vol'   # High volatility regime
		
		return regimes
	
	def train_simple_linear_model(self, features: pd.DataFrame, 
		target_returns: pd.Series) -> Dict[str, float]:
		"""Train simple linear model (Feature 02 requirement)"""
		
		try:
			if features.empty or target_returns.empty:
				self.logger.warning("Insufficient data for training")
				return {}
			
			# Align features and targets
			aligned_data = features.join(target_returns, how='inner')
			
			if len(aligned_data) < 100:
				self.logger.warning(f"Insufficient aligned data: {len(aligned_data)}")
				return {}
			
			X = aligned_data.iloc[:, :-1]  # Features
			y = aligned_data.iloc[:, -1]   # Target returns
			
			# Create binary classification targets (up/down)
			y_binary = (y > 0).astype(int)
			
			# Train/test split
			X_train, X_test, y_train, y_test = train_test_split(
				X, y_binary, test_size=0.3, random_state=42, shuffle=False
			)
			
			# Scale features
			X_train_scaled = self.scaler.fit_transform(X_train)
			X_test_scaled = self.scaler.transform(X_test)
			
			# Train linear model
			self.linear_model.fit(X_train_scaled, y_train)
			
			# Evaluate
			y_pred = self.linear_model.predict(X_test_scaled)
			y_pred_binary = (y_pred > 0.5).astype(int)
			
			accuracy = accuracy_score(y_test, y_pred_binary)
			precision = precision_score(y_test, y_pred_binary, zero_division=0)
			recall = recall_score(y_test, y_pred_binary, zero_division=0)
			
			self.is_trained = True
			
			results = {
				'accuracy': accuracy,
				'precision': precision,
				'recall': recall,
				'n_features': X.shape[1],
				'n_samples': len(aligned_data)
			}
			
			self.logger.info(f"Linear model trained: {accuracy:.3f} accuracy")
			return results
			
		except Exception as e:
			self.logger.error(f"Error training linear model: {e}")
			return {}
	
	def generate_signal_score(self, current_features: pd.DataFrame) -> float:
		"""Generate signal score 1-10 (Feature 02 requirement)"""
		
		try:
			if not self.is_trained or current_features.empty:
				return 5.0  # Neutral score
			
			# Scale features
			features_scaled = self.scaler.transform(current_features.iloc[[-1]])
			
			# Get prediction probability
			prediction = self.linear_model.predict(features_scaled)[0]
			
			# Convert to 1-10 scale using percentiles
			score = 1 + (prediction * 9)  # Scale 0-1 prediction to 1-10
			score = max(1.0, min(10.0, score))  # Clamp to valid range
			
			return float(score)
			
		except Exception as e:
			self.logger.error(f"Error generating signal score: {e}")
			return 5.0
	
	def calculate_position_size(self, signal_score: float, vix_level: float, 
		current_exposure: float = 0.0) -> float:
		"""Calculate position size based on signal and VIX (Feature 02 requirement)"""
		
		try:
			# Base position size from VIX regime
			base_size = 0.01  # Default 1%
			
			for regime, config in self.vix_sizing.items():
				if vix_level <= config['vix_max']:
					base_size = config['position_size']
					break
			
			# Scale by signal strength (linear scaling)
			signal_multiplier = signal_score / 10.0
			position_size = base_size * signal_multiplier
			
			# Apply hard limits
			position_size = min(position_size, self.max_position_size)
			
			# Check total exposure limit
			if current_exposure + position_size > self.max_total_exposure:
				position_size = max(0, self.max_total_exposure - current_exposure)
			
			return position_size
			
		except Exception as e:
			self.logger.error(f"Error calculating position size: {e}")
			return 0.0
	
	def apply_simple_kelly(self, win_rate: float, avg_win: float, 
		avg_loss: float) -> float:
		"""Apply simple Kelly criterion (Feature 02 requirement)"""
		
		try:
			if win_rate <= 0.5 or avg_win <= 0 or avg_loss <= 0:
				return 0.0  # No position if not profitable
			
			# Kelly formula: f = (bp - q) / b
			# where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
			b = avg_win / avg_loss
			p = win_rate
			q = 1 - win_rate
			
			kelly_fraction = (b * p - q) / b
			
			# Conservative Kelly (use 25% of full Kelly)
			conservative_kelly = kelly_fraction * 0.25
			
			# Cap at reasonable limits
			return max(0.0, min(0.05, conservative_kelly))  # Max 5%
			
		except Exception as e:
			self.logger.error(f"Error calculating Kelly criterion: {e}")
			return 0.0
	
	def detect_signal_threshold(self, signal_score: float) -> str:
		"""Detect signal threshold (Feature 02 requirement)"""
		
		if signal_score >= self.signal_thresholds['NOW']:
			return 'NOW'
		elif signal_score >= self.signal_thresholds['SOON']:
			return 'SOON'
		elif signal_score >= self.signal_thresholds['WATCH']:
			return 'WATCH'
		else:
			return 'NEUTRAL'
	
	def save_model(self, model_dir: str = "models"):
		"""Save trained model"""
		try:
			os.makedirs(model_dir, exist_ok=True)
			
			if self.is_trained:
				joblib.dump(self.linear_model, f"{model_dir}/linear_model.pkl")
				joblib.dump(self.scaler, f"{model_dir}/scaler.pkl")
				self.logger.info("Signal generation model saved")
				
		except Exception as e:
			self.logger.error(f"Error saving model: {e}")
	
	def load_model(self, model_dir: str = "models"):
		"""Load trained model"""
		try:
			model_path = f"{model_dir}/linear_model.pkl"
			scaler_path = f"{model_dir}/scaler.pkl"
			
			if os.path.exists(model_path) and os.path.exists(scaler_path):
				self.linear_model = joblib.load(model_path)
				self.scaler = joblib.load(scaler_path)
				self.is_trained = True
				self.logger.info("Signal generation model loaded")
				return True
			else:
				self.logger.warning("Model files not found")
				return False
				
		except Exception as e:
			self.logger.error(f"Error loading model: {e}")
			return False
