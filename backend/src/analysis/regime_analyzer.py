"""
Simple Market Regime Analysis for Historical Signal Performance
Manual date-based period analysis instead of complex ML clustering
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

class RegimeAnalyzer:
	"""Simple date-based market regime analysis"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.market_regimes = self._define_market_periods()
		
	def _define_market_periods(self) -> Dict[str, Dict]:
		"""Define major market periods for analysis"""
		return {
			'covid_crash': {
				'start': '2020-02-01',
				'end': '2020-04-30',
				'description': 'COVID-19 Market Crash',
				'characteristics': 'High volatility, flight to quality, tech weakness'
			},
			'covid_recovery': {
				'start': '2020-05-01', 
				'end': '2021-12-31',
				'description': 'COVID Recovery Rally',
				'characteristics': 'QE-driven rally, tech strength, low rates'
			},
			'rate_hike_cycle': {
				'start': '2022-01-01',
				'end': '2023-06-30',
				'description': 'Fed Rate Hiking Cycle',
				'characteristics': 'Rising rates, bond stress, growth concerns'
			},
			'ai_boom': {
				'start': '2023-07-01',
				'end': '2024-12-31', 
				'description': 'AI and Chip Boom',
				'characteristics': 'AI hype, semiconductor strength, selective rally'
			},
			'current_period': {
				'start': '2025-01-01',
				'end': '2025-12-31',
				'description': 'Current Trading Period',
				'characteristics': 'Active signal generation period'
			}
		}
		
	def classify_signals_by_regime(self, signals_df: pd.DataFrame) -> pd.DataFrame:
		"""Add regime classification to signals data"""
		if 'timestamp' not in signals_df.columns:
			self.logger.error("Signals dataframe must have 'timestamp' column")
			return signals_df
			
		signals_with_regime = signals_df.copy()
		signals_with_regime['timestamp'] = pd.to_datetime(signals_with_regime['timestamp'])
		signals_with_regime['regime'] = 'unknown'
		signals_with_regime['regime_description'] = 'Unknown Period'
		
		# Classify each signal by regime
		for regime_name, regime_info in self.market_regimes.items():
			start_date = pd.to_datetime(regime_info['start'])
			end_date = pd.to_datetime(regime_info['end'])
			
			mask = (signals_with_regime['timestamp'] >= start_date) & \
				   (signals_with_regime['timestamp'] <= end_date)
			
			signals_with_regime.loc[mask, 'regime'] = regime_name
			signals_with_regime.loc[mask, 'regime_description'] = regime_info['description']
			
		return signals_with_regime
		
	def analyze_regime_performance(self, returns_df: pd.DataFrame) -> Dict[str, Any]:
		"""Analyze performance by market regime"""
		if 'regime' not in returns_df.columns:
			returns_df = self.classify_signals_by_regime(returns_df)
			
		regime_performance = {}
		
		for regime in returns_df['regime'].unique():
			regime_data = returns_df[returns_df['regime'] == regime]
			
			if regime_data.empty:
				continue
				
			# Basic performance metrics by regime
			performance = {
				'total_signals': len(regime_data),
				'win_rate': regime_data['win'].mean() if 'win' in regime_data.columns else 0,
				'avg_return': regime_data['return_pct'].mean() if 'return_pct' in regime_data.columns else 0,
				'total_pnl': regime_data['profit_loss'].sum() if 'profit_loss' in regime_data.columns else 0,
				'return_volatility': regime_data['return_pct'].std() if 'return_pct' in regime_data.columns else 0,
				'best_signal': regime_data['return_pct'].max() if 'return_pct' in regime_data.columns else 0,
				'worst_signal': regime_data['return_pct'].min() if 'return_pct' in regime_data.columns else 0,
				'regime_info': self.market_regimes.get(regime, {})
			}
			
			# Signal type breakdown
			if 'signal_type' in regime_data.columns:
				signal_breakdown = regime_data.groupby('signal_type').agg({
					'return_pct': 'mean',
					'win': 'mean' if 'win' in regime_data.columns else 'count'
				}).to_dict()
				performance['signal_type_breakdown'] = signal_breakdown
				
			# Symbol performance in this regime
			if 'symbol' in regime_data.columns:
				symbol_performance = regime_data.groupby('symbol').agg({
					'return_pct': 'mean',
					'win': 'mean' if 'win' in regime_data.columns else 'count'
				}).to_dict()
				performance['symbol_performance'] = symbol_performance
				
			regime_performance[regime] = performance
			
		return regime_performance
		
	def find_similar_periods(self, current_conditions: Dict[str, float], 
							historical_data: pd.DataFrame) -> List[Dict]:
		"""Find historically similar market conditions"""
		# Simple similarity based on bond market conditions
		similar_periods = []
		
		if historical_data.empty:
			return similar_periods
			
		# Look for periods with similar bond stress characteristics
		target_yield_spread = current_conditions.get('yield_curve_spread', 0)
		target_volatility = current_conditions.get('bond_volatility', 0)
		
		# Group by month and find similar conditions
		historical_data['month'] = pd.to_datetime(historical_data['timestamp']).dt.to_period('M')
		monthly_conditions = historical_data.groupby('month').agg({
			'yield_curve_spread': 'mean',
			'bond_volatility': 'mean',
			'confidence_score': 'mean',
			'return_pct': 'mean'
		}).reset_index()
		
		# Calculate similarity scores
		for _, period in monthly_conditions.iterrows():
			yield_diff = abs(period['yield_curve_spread'] - target_yield_spread)
			vol_diff = abs(period['bond_volatility'] - target_volatility)
			
			# Simple distance metric
			similarity_score = 1 / (1 + yield_diff + vol_diff)
			
			similar_periods.append({
				'period': str(period['month']),
				'similarity_score': similarity_score,
				'historical_conditions': {
					'yield_curve_spread': period['yield_curve_spread'],
					'bond_volatility': period['bond_volatility'],
					'avg_confidence': period['confidence_score']
				},
				'historical_performance': {
					'avg_return': period['return_pct']
				}
			})
			
		# Sort by similarity and return top matches
		similar_periods.sort(key=lambda x: x['similarity_score'], reverse=True)
		return similar_periods[:5]  # Top 5 similar periods
		
	def generate_regime_report(self, signals_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict[str, Any]:
		"""Generate comprehensive regime analysis report"""
		# Classify data by regime
		classified_signals = self.classify_signals_by_regime(signals_df)
		classified_returns = self.classify_signals_by_regime(returns_df) if not returns_df.empty else pd.DataFrame()
		
		# Analyze performance by regime
		regime_performance = self.analyze_regime_performance(classified_returns) if not classified_returns.empty else {}
		
		# Signal generation patterns by regime
		signal_patterns = self._analyze_signal_patterns(classified_signals)
		
		# Current market assessment
		current_assessment = self._assess_current_regime()
		
		return {
			'regime_definitions': self.market_regimes,
			'regime_performance': regime_performance,
			'signal_generation_patterns': signal_patterns,
			'current_market_assessment': current_assessment,
			'total_signals_analyzed': len(classified_signals),
			'regimes_with_data': list(classified_signals['regime'].unique()),
			'analysis_timestamp': datetime.now().isoformat()
		}
		
	def _analyze_signal_patterns(self, signals_df: pd.DataFrame) -> Dict[str, Any]:
		"""Analyze signal generation patterns by regime"""
		patterns = {}
		
		for regime in signals_df['regime'].unique():
			regime_signals = signals_df[signals_df['regime'] == regime]
			
			patterns[regime] = {
				'total_signals': len(regime_signals),
				'signals_per_month': len(regime_signals) / max(1, self._calculate_regime_months(regime)),
				'signal_type_distribution': regime_signals['signal_type'].value_counts().to_dict() if 'signal_type' in regime_signals.columns else {},
				'avg_confidence': regime_signals['confidence_score'].mean() if 'confidence_score' in regime_signals.columns else 0,
				'most_active_symbols': regime_signals['symbol'].value_counts().head(3).to_dict() if 'symbol' in regime_signals.columns else {}
			}
			
		return patterns
		
	def _calculate_regime_months(self, regime: str) -> int:
		"""Calculate number of months in a regime period"""
		if regime not in self.market_regimes:
			return 1
			
		start = pd.to_datetime(self.market_regimes[regime]['start'])
		end = pd.to_datetime(self.market_regimes[regime]['end'])
		return max(1, (end - start).days // 30)
		
	def _assess_current_regime(self) -> Dict[str, Any]:
		"""Assess current market regime characteristics"""
		current_date = datetime.now()
		
		# Find current regime
		current_regime = 'unknown'
		for regime_name, regime_info in self.market_regimes.items():
			start = pd.to_datetime(regime_info['start'])
			end = pd.to_datetime(regime_info['end'])
			
			if start <= current_date <= end:
				current_regime = regime_name
				break
				
		return {
			'current_regime': current_regime,
			'regime_description': self.market_regimes.get(current_regime, {}).get('description', 'Unknown'),
			'regime_characteristics': self.market_regimes.get(current_regime, {}).get('characteristics', 'Unknown'),
			'days_in_regime': (current_date - pd.to_datetime(self.market_regimes.get(current_regime, {}).get('start', current_date))).days if current_regime != 'unknown' else 0,
			'assessment_date': current_date.isoformat()
		}
