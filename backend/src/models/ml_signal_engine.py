import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

class MLSignalEngine:
	"""Machine learning engine for bond stress anomaly detection and signal prediction"""
	
	def __init__(self, model_path: str = "models/"):
		self.logger = logging.getLogger(__name__)
		self.model_path = model_path
		os.makedirs(model_path, exist_ok=True)
		
		# Initialize models
		self.anomaly_detector = IsolationForest(
			contamination=0.1,  # 10% of data expected to be anomalies
			random_state=42,
			n_estimators=100
		)
		
		self.signal_predictor = RandomForestRegressor(
			n_estimators=200,
			max_depth=10,
			random_state=42,
			min_samples_split=5
		)
		
		self.scaler = StandardScaler()
		self.is_fitted = False
		
	def prepare_features(self, 
		yield_curve_data: pd.Series,
		bond_volatility: pd.Series,
		credit_spreads: pd.Series,
		vix_data: pd.Series = None
	) -> pd.DataFrame:
		"""Prepare feature matrix for ML models"""
		
		try:
			# Combine all data into a single DataFrame
			features_df = pd.DataFrame(index=yield_curve_data.index)
			
			# Core bond stress features
			features_df['yield_spread'] = yield_curve_data
			features_df['bond_volatility'] = bond_volatility
			features_df['credit_spreads'] = credit_spreads
			
			# Rolling statistics (20-day and 60-day lookbacks)
			for window in [20, 60]:
				features_df[f'yield_spread_ma_{window}'] = yield_curve_data.rolling(window).mean()
				features_df[f'yield_spread_std_{window}'] = yield_curve_data.rolling(window).std()
				features_df[f'yield_spread_zscore_{window}'] = (
					yield_curve_data - yield_curve_data.rolling(window).mean()
				) / yield_curve_data.rolling(window).std()
				
				features_df[f'bond_vol_ma_{window}'] = bond_volatility.rolling(window).mean()
				features_df[f'bond_vol_zscore_{window}'] = (
					bond_volatility - bond_volatility.rolling(window).mean()
				) / bond_volatility.rolling(window).std()
			
			# Momentum indicators
			for lag in [1, 5, 10, 20]:
				features_df[f'yield_spread_lag_{lag}'] = yield_curve_data.shift(lag)
				features_df[f'yield_spread_change_{lag}'] = yield_curve_data.diff(lag)
				features_df[f'bond_vol_change_{lag}'] = bond_volatility.diff(lag)
			
			# VIX features if available
			if vix_data is not None and not vix_data.empty:
				aligned_vix = vix_data.reindex(features_df.index, method='ffill')
				features_df['vix'] = aligned_vix
				features_df['vix_ma_20'] = aligned_vix.rolling(20).mean()
				features_df['vix_zscore_20'] = (aligned_vix - aligned_vix.rolling(20).mean()) / aligned_vix.rolling(20).std()
			
			# Interaction features
			features_df['yield_vol_interaction'] = features_df['yield_spread'] * features_df['bond_volatility']
			features_df['stress_composite'] = (
				features_df['yield_spread_zscore_20'] * -1 +  # Negative because inversion is stress
				features_df['bond_vol_zscore_20'] +
				features_df['credit_spreads']
			) / 3
			
			# Drop rows with NaN values
			features_df = features_df.dropna()
			
			self.logger.info(f"Prepared feature matrix: {features_df.shape[0]} samples, {features_df.shape[1]} features")
			return features_df
			
		except Exception as e:
			self.logger.error(f"Error preparing features: {e}")
			return pd.DataFrame()
	
	def detect_bond_stress_anomalies(self, features_df: pd.DataFrame) -> pd.Series:
		"""Detect bond market stress anomalies using Isolation Forest"""
		
		try:
			if features_df.empty:
				return pd.Series()
			
			# Scale features
			features_scaled = self.scaler.fit_transform(features_df)
			
			# Detect anomalies
			anomaly_scores = self.anomaly_detector.fit_predict(features_scaled)
			anomaly_proba = self.anomaly_detector.decision_function(features_scaled)
			
			# Convert to pandas Series
			anomalies = pd.Series(
				anomaly_scores, 
				index=features_df.index,
				name='anomaly_flag'
			)
			
			anomaly_strength = pd.Series(
				anomaly_proba,
				index=features_df.index,
				name='anomaly_strength'
			)
			
			# Combine into results
			results = pd.DataFrame({
				'anomaly_flag': anomalies,
				'anomaly_strength': anomaly_strength,
				'anomaly_percentile': anomaly_strength.rank(pct=True)
			})
			
			n_anomalies = (anomalies == -1).sum()
			self.logger.info(f"Detected {n_anomalies} anomalies out of {len(anomalies)} observations")
			
			return results
			
		except Exception as e:
			self.logger.error(f"Error detecting anomalies: {e}")
			return pd.Series()
	
	def train_signal_strength_predictor(self, 
		features_df: pd.DataFrame,
		target_returns: pd.Series,
		ai_chip_symbols: List[str] = ['NVDA', 'AMD', 'TSM']
	) -> Dict[str, float]:
		"""Train Random Forest model to predict signal strength"""
		
		try:
			if features_df.empty or target_returns.empty:
				self.logger.warning("Insufficient data for training")
				return {}
			
			# Align features and targets
			aligned_data = features_df.join(target_returns, how='inner')
			
			if len(aligned_data) < 100:
				self.logger.warning(f"Insufficient aligned data: {len(aligned_data)} samples")
				return {}
			
			X = aligned_data.iloc[:, :-1]  # Features
			y = aligned_data.iloc[:, -1]   # Target returns
			
			# Create signal strength labels based on future returns
			# Strong positive signal: returns > 75th percentile
			# Strong negative signal: returns < 25th percentile
			signal_strength = pd.cut(
				y, 
				bins=[-np.inf, y.quantile(0.25), y.quantile(0.75), np.inf],
				labels=[0, 1, 2]  # 0=sell, 1=hold, 2=buy
			)
			
			# Scale features
			X_scaled = self.scaler.fit_transform(X)
			
			# Time series cross-validation
			tscv = TimeSeriesSplit(n_splits=5)
			cv_scores = []
			
			for train_idx, test_idx in tscv.split(X_scaled):
				X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
				y_train, y_test = signal_strength.iloc[train_idx], signal_strength.iloc[test_idx]
				
				# Train model
				self.signal_predictor.fit(X_train, y_train)
				
				# Predict and score
				y_pred = self.signal_predictor.predict(X_test)
				score = accuracy_score(y_test, np.round(y_pred))
				cv_scores.append(score)
			
			# Final training on all data
			self.signal_predictor.fit(X_scaled, signal_strength)
			self.is_fitted = True
			
			# Feature importance
			feature_importance = dict(zip(
				X.columns, 
				self.signal_predictor.feature_importances_
			))
			
			# Sort by importance
			feature_importance = dict(sorted(
				feature_importance.items(), 
				key=lambda x: x[1], 
				reverse=True
			))
			
			results = {
				'cv_accuracy_mean': np.mean(cv_scores),
				'cv_accuracy_std': np.std(cv_scores),
				'feature_importance': feature_importance,
				'n_samples': len(aligned_data)
			}
			
			self.logger.info(f"Signal predictor trained: {results['cv_accuracy_mean']:.3f} ± {results['cv_accuracy_std']:.3f} accuracy")
			
			return results
			
		except Exception as e:
			self.logger.error(f"Error training signal predictor: {e}")
			return {}
	
	def predict_signal_strength(self, current_features: pd.DataFrame) -> Dict[str, float]:
		"""Predict signal strength for current market conditions"""
		
		try:
			if not self.is_fitted:
				self.logger.warning("Model not trained yet")
				return {'signal_strength': 1.0, 'confidence': 0.0}
			
			if current_features.empty:
				return {'signal_strength': 1.0, 'confidence': 0.0}
			
			# Scale features
			features_scaled = self.scaler.transform(current_features.iloc[[-1]])
			
			# Predict signal strength
			signal_pred = self.signal_predictor.predict(features_scaled)[0]
			
			# Get prediction confidence from ensemble variance
			tree_predictions = np.array([
				tree.predict(features_scaled)[0] 
				for tree in self.signal_predictor.estimators_
			])
			
			confidence = 1.0 - (np.std(tree_predictions) / np.mean(tree_predictions + 1e-6))
			confidence = max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0
			
			return {
				'signal_strength': float(signal_pred),
				'confidence': float(confidence),
				'prediction_variance': float(np.var(tree_predictions))
			}
			
		except Exception as e:
			self.logger.error(f"Error predicting signal strength: {e}")
			return {'signal_strength': 1.0, 'confidence': 0.0}
	
	def detect_market_regime(self, features_df: pd.DataFrame, window: int = 60) -> pd.Series:
		"""Detect market regime (bull/bear/neutral) using clustering"""
		
		try:
			if features_df.empty or len(features_df) < window:
				return pd.Series()
			
			# Use rolling volatility and trend for regime detection
			rolling_vol = features_df['bond_volatility'].rolling(window).std()
			rolling_trend = features_df['yield_spread'].rolling(window).mean().diff(window)
			
			# Simple regime classification
			regimes = pd.Series(index=features_df.index, name='market_regime')
			
			for i in range(window, len(features_df)):
				vol = rolling_vol.iloc[i]
				trend = rolling_trend.iloc[i]
				
				if pd.isna(vol) or pd.isna(trend):
					regimes.iloc[i] = 'neutral'
					continue
				
				vol_percentile = rolling_vol.iloc[:i+1].rank(pct=True).iloc[-1]
				trend_percentile = rolling_trend.iloc[:i+1].rank(pct=True).iloc[-1]
				
				if vol_percentile > 0.7:  # High volatility
					regimes.iloc[i] = 'stress'
				elif trend_percentile < 0.3:  # Declining trend
					regimes.iloc[i] = 'bearish'
				elif trend_percentile > 0.7:  # Rising trend
					regimes.iloc[i] = 'bullish'
				else:
					regimes.iloc[i] = 'neutral'
			
			self.logger.info(f"Market regime detection completed. Current regime: {regimes.iloc[-1] if not regimes.empty else 'unknown'}")
			
			return regimes
			
		except Exception as e:
			self.logger.error(f"Error detecting market regime: {e}")
			return pd.Series()
	
	def save_models(self):
		"""Save trained models to disk"""
		try:
			if self.is_fitted:
				joblib.dump(self.signal_predictor, os.path.join(self.model_path, 'signal_predictor.pkl'))
				joblib.dump(self.scaler, os.path.join(self.model_path, 'feature_scaler.pkl'))
				joblib.dump(self.anomaly_detector, os.path.join(self.model_path, 'anomaly_detector.pkl'))
				self.logger.info("Models saved successfully")
		except Exception as e:
			self.logger.error(f"Error saving models: {e}")
	
	def load_models(self):
		"""Load trained models from disk"""
		try:
			predictor_path = os.path.join(self.model_path, 'signal_predictor.pkl')
			scaler_path = os.path.join(self.model_path, 'feature_scaler.pkl')
			anomaly_path = os.path.join(self.model_path, 'anomaly_detector.pkl')
			
			if all(os.path.exists(path) for path in [predictor_path, scaler_path, anomaly_path]):
				self.signal_predictor = joblib.load(predictor_path)
				self.scaler = joblib.load(scaler_path)
				self.anomaly_detector = joblib.load(anomaly_path)
				self.is_fitted = True
				self.logger.info("Models loaded successfully")
				return True
			else:
				self.logger.warning("Model files not found")
				return False
		except Exception as e:
			self.logger.error(f"Error loading models: {e}")
			return False
