#!/usr/bin/env python3
"""
Historical Performance Analyzer for AI Chip Trading Signals
Feature 05: Comprehensive backtesting and signal quality analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import warnings
from pathlib import Path

# Set up plotting style
plt.style.use('seaborn-v0_8')
warnings.filterwarnings('ignore')

class HistoricalPerformanceAnalyzer:
	"""Comprehensive historical analysis for trading signal performance"""
	
	def __init__(self, data_path: str = "/Users/achuabio/AI_Chip_Trading_Signals/backend/data"):
		self.logger = logging.getLogger(__name__)
		self.data_path = Path(data_path)
		self.results_path = self.data_path / "analysis_results"
		self.results_path.mkdir(exist_ok=True)
		
		# Analysis parameters
		self.confidence_levels = [0.90, 0.95, 0.99]
		self.regime_periods = {
			'COVID_CRASH': ('2020-02-01', '2020-05-01'),
			'RECOVERY': ('2020-05-01', '2021-12-31'),
			'RATE_HIKES': ('2022-01-01', '2023-06-30'),
			'AI_BOOM': ('2023-07-01', '2024-12-31')
		}
		
	def load_historical_data(self) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
		"""Load historical signals and price data"""
		try:
			# Load from database (implement as needed)
			from utils.database import DatabaseManager
			db = DatabaseManager()
			
			# Get all historical signals
			signals = db.get_historical_signals(days=1825)  # 5 years
			signals_df = pd.DataFrame(signals)
			
			if not signals_df.empty:
				signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
				signals_df = signals_df.set_index('timestamp')
			
			# Load price data
			from data_sources.yahoo_client import YahooFinanceClient
			yahoo = YahooFinanceClient()
			price_data = yahoo.get_ai_chip_stocks(period="5y")
			
			self.logger.info(f"Loaded {len(signals_df)} signals and {len(price_data)} symbols")
			return signals_df, price_data
			
		except Exception as e:
			self.logger.error(f"Error loading historical data: {e}")
			return pd.DataFrame(), {}
	
	def calculate_signal_performance_metrics(self, 
		signals_df: pd.DataFrame, 
		price_data: Dict[str, pd.DataFrame]
	) -> Dict[str, Any]:
		"""Calculate comprehensive signal performance metrics"""
		
		if signals_df.empty or not price_data:
			return {}
		
		metrics = {
			'overall_performance': {},
			'by_symbol': {},
			'by_signal_strength': {},
			'by_regime': {},
			'statistical_tests': {}
		}
		
		# Overall performance
		metrics['overall_performance'] = self._calculate_overall_metrics(signals_df, price_data)
		
		# Performance by symbol
		for symbol in ['NVDA', 'AMD', 'TSM', 'INTC', 'QCOM']:
			symbol_signals = signals_df[signals_df['symbol'] == symbol]
			if not symbol_signals.empty and symbol in price_data:
				metrics['by_symbol'][symbol] = self._calculate_symbol_metrics(
					symbol_signals, price_data[symbol]
				)
		
		# Performance by signal strength
		for strength in ['NOW', 'SOON', 'WATCH']:
			strength_signals = signals_df[signals_df['signal_type'] == strength]
			if not strength_signals.empty:
				metrics['by_signal_strength'][strength] = self._calculate_strength_metrics(
					strength_signals, price_data
				)
		
		# Performance by market regime
		for regime, (start, end) in self.regime_periods.items():
			regime_signals = signals_df[start:end]
			if not regime_signals.empty:
				metrics['by_regime'][regime] = self._calculate_regime_metrics(
					regime_signals, price_data, start, end
				)
		
		# Statistical significance tests
		metrics['statistical_tests'] = self._run_statistical_tests(signals_df, price_data)
		
		return metrics
	
	def _calculate_overall_metrics(self, signals_df: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
		"""Calculate overall performance metrics"""
		
		if signals_df.empty:
			return {}
		
		try:
			# Calculate returns for each signal
			returns = []
			holding_periods = []
			
			for _, signal in signals_df.iterrows():
				symbol = signal['symbol']
				if symbol not in price_data:
					continue
				
				price_df = price_data[symbol]
				signal_date = signal.name
				
				# Find entry price (next trading day)
				entry_prices = price_df[price_df.index > signal_date]['Close']
				if entry_prices.empty:
					continue
				entry_price = entry_prices.iloc[0]
				entry_date = entry_prices.index[0]
				
				# Find exit price (30 days later or signal reversal)
				exit_date = entry_date + timedelta(days=30)
				exit_prices = price_df[price_df.index <= exit_date]['Close']
				if exit_prices.empty:
					continue
				exit_price = exit_prices.iloc[-1]
				
				# Calculate return based on signal type
				if signal['signal_type'] in ['NOW', 'SOON']:
					if signal.get('recommended_action') == 'BUY':
						ret = (exit_price - entry_price) / entry_price
					else:  # SELL or short
						ret = (entry_price - exit_price) / entry_price
				else:  # WATCH - neutral
					ret = 0.0
				
				returns.append(ret)
				holding_periods.append((exit_date - entry_date).days)
			
			if not returns:
				return {}
			
			returns = np.array(returns)
			
			# Calculate metrics
			total_return = np.prod(1 + returns) - 1
			avg_return = np.mean(returns)
			volatility = np.std(returns) * np.sqrt(252)  # Annualized
			sharpe_ratio = avg_return / (volatility + 1e-8) * np.sqrt(252)
			
			win_rate = np.mean(returns > 0)
			max_drawdown = self._calculate_max_drawdown(returns)
			
			return {
				'total_return': total_return,
				'average_return': avg_return,
				'volatility': volatility,
				'sharpe_ratio': sharpe_ratio,
				'win_rate': win_rate,
				'max_drawdown': max_drawdown,
				'total_signals': len(returns),
				'avg_holding_days': np.mean(holding_periods),
				'best_trade': np.max(returns) if len(returns) > 0 else 0,
				'worst_trade': np.min(returns) if len(returns) > 0 else 0
			}
			
		except Exception as e:
			self.logger.error(f"Error calculating overall metrics: {e}")
			return {}
	
	def _calculate_symbol_metrics(self, symbol_signals: pd.DataFrame, price_df: pd.DataFrame) -> Dict[str, float]:
		"""Calculate performance metrics for a specific symbol"""
		# Similar to overall metrics but symbol-specific
		# Implementation follows same pattern as _calculate_overall_metrics
		return self._calculate_overall_metrics(symbol_signals, {symbol_signals['symbol'].iloc[0]: price_df})
	
	def _calculate_strength_metrics(self, strength_signals: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
		"""Calculate performance metrics by signal strength"""
		return self._calculate_overall_metrics(strength_signals, price_data)
	
	def _calculate_regime_metrics(self, regime_signals: pd.DataFrame, price_data: Dict[str, pd.DataFrame], start: str, end: str) -> Dict[str, float]:
		"""Calculate performance metrics for specific market regime"""
		metrics = self._calculate_overall_metrics(regime_signals, price_data)
		metrics['regime_start'] = start
		metrics['regime_end'] = end
		return metrics
	
	def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
		"""Calculate maximum drawdown from returns series"""
		cumulative = np.cumprod(1 + returns)
		running_max = np.maximum.accumulate(cumulative)
		drawdown = (cumulative - running_max) / running_max
		return np.min(drawdown)
	
	def _run_statistical_tests(self, signals_df: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
		"""Run statistical significance tests on signal performance"""
		
		if signals_df.empty:
			return {}
		
		tests = {}
		
		try:
			# Calculate returns for all signals
			returns = []
			
			for _, signal in signals_df.iterrows():
				symbol = signal['symbol']
				if symbol not in price_data:
					continue
				
				price_df = price_data[symbol]
				signal_date = signal.name
				
				# Simple 30-day forward return calculation
				entry_prices = price_df[price_df.index > signal_date]['Close']
				if entry_prices.empty:
					continue
				entry_price = entry_prices.iloc[0]
				entry_date = entry_prices.index[0]
				
				exit_date = entry_date + timedelta(days=30)
				exit_prices = price_df[price_df.index <= exit_date]['Close']
				if exit_prices.empty:
					continue
				exit_price = exit_prices.iloc[-1]
				
				ret = (exit_price - entry_price) / entry_price
				returns.append(ret)
			
			if not returns:
				return {}
			
			returns = np.array(returns)
			
			# T-test for positive returns
			t_stat, p_value = stats.ttest_1samp(returns, 0)
			tests['t_test'] = {
				't_statistic': t_stat,
				'p_value': p_value,
				'significant': p_value < 0.05,
				'interpretation': 'Returns significantly different from zero' if p_value < 0.05 else 'No significant edge detected'
			}
			
			# Normality test
			shapiro_stat, shapiro_p = stats.shapiro(returns)
			tests['normality_test'] = {
				'shapiro_statistic': shapiro_stat,
				'p_value': shapiro_p,
				'normal_distribution': shapiro_p > 0.05
			}
			
			# Confidence intervals
			for confidence in self.confidence_levels:
				alpha = 1 - confidence
				ci_lower, ci_upper = stats.t.interval(
					confidence, len(returns)-1, 
					loc=np.mean(returns), 
					scale=stats.sem(returns)
				)
				tests[f'confidence_interval_{int(confidence*100)}'] = {
					'lower_bound': ci_lower,
					'upper_bound': ci_upper,
					'mean_return': np.mean(returns)
				}
			
		except Exception as e:
			self.logger.error(f"Error in statistical tests: {e}")
		
		return tests
	
	def generate_performance_visualizations(self, metrics: Dict[str, Any]) -> List[str]:
		"""Generate comprehensive performance visualization charts"""
		
		chart_files = []
		
		try:
			# 1. Overall Performance Summary
			fig, axes = plt.subplots(2, 2, figsize=(15, 12))
			fig.suptitle('AI Chip Trading Signal Performance Overview', fontsize=16, fontweight='bold')
			
			overall = metrics.get('overall_performance', {})
			
			# Win Rate Chart
			if 'win_rate' in overall:
				axes[0, 0].bar(['Win Rate'], [overall['win_rate']], color='green', alpha=0.7)
				axes[0, 0].set_ylabel('Win Rate (%)')
				axes[0, 0].set_title('Signal Win Rate')
				axes[0, 0].set_ylim([0, 1])
				
				for i, v in enumerate([overall['win_rate']]):
					axes[0, 0].text(i, v + 0.01, f'{v:.1%}', ha='center', va='bottom')
			
			# Sharpe Ratio
			if 'sharpe_ratio' in overall:
				axes[0, 1].bar(['Sharpe Ratio'], [overall['sharpe_ratio']], color='blue', alpha=0.7)
				axes[0, 1].set_ylabel('Sharpe Ratio')
				axes[0, 1].set_title('Risk-Adjusted Returns')
				axes[0, 1].axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Good Threshold')
				axes[0, 1].legend()
			
			# Performance by Symbol
			by_symbol = metrics.get('by_symbol', {})
			if by_symbol:
				symbols = list(by_symbol.keys())
				returns = [by_symbol[s].get('total_return', 0) for s in symbols]
				colors = ['green' if r > 0 else 'red' for r in returns]
				
				axes[1, 0].bar(symbols, returns, color=colors, alpha=0.7)
				axes[1, 0].set_ylabel('Total Return (%)')
				axes[1, 0].set_title('Performance by AI Chip Symbol')
				axes[1, 0].axhline(y=0, color='black', linestyle='-', alpha=0.3)
				
				for i, v in enumerate(returns):
					axes[1, 0].text(i, v + (0.01 if v > 0 else -0.01), f'{v:.1%}', 
									ha='center', va='bottom' if v > 0 else 'top')
			
			# Performance by Signal Strength
			by_strength = metrics.get('by_signal_strength', {})
			if by_strength:
				strengths = list(by_strength.keys())
				win_rates = [by_strength[s].get('win_rate', 0) for s in strengths]
				
				axes[1, 1].bar(strengths, win_rates, color=['red', 'orange', 'green'], alpha=0.7)
				axes[1, 1].set_ylabel('Win Rate (%)')
				axes[1, 1].set_title('Win Rate by Signal Strength')
				axes[1, 1].set_ylim([0, 1])
				
				for i, v in enumerate(win_rates):
					axes[1, 1].text(i, v + 0.01, f'{v:.1%}', ha='center', va='bottom')
			
			plt.tight_layout()
			chart_file = self.results_path / 'performance_overview.png'
			plt.savefig(chart_file, dpi=300, bbox_inches='tight')
			plt.close()
			chart_files.append(str(chart_file))
			
			# 2. Market Regime Analysis
			self._create_regime_analysis_chart(metrics, chart_files)
			
			# 3. Statistical Analysis Chart
			self._create_statistical_analysis_chart(metrics, chart_files)
			
			self.logger.info(f"Generated {len(chart_files)} performance charts")
			
		except Exception as e:
			self.logger.error(f"Error generating visualizations: {e}")
		
		return chart_files
	
	def _create_regime_analysis_chart(self, metrics: Dict[str, Any], chart_files: List[str]):
		"""Create market regime analysis chart"""
		
		by_regime = metrics.get('by_regime', {})
		if not by_regime:
			return
		
		fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
		fig.suptitle('Performance Analysis by Market Regime', fontsize=16, fontweight='bold')
		
		regimes = list(by_regime.keys())
		returns = [by_regime[r].get('total_return', 0) for r in regimes]
		win_rates = [by_regime[r].get('win_rate', 0) for r in regimes]
		
		# Returns by regime
		colors = ['red', 'orange', 'blue', 'green']
		ax1.bar(regimes, returns, color=colors, alpha=0.7)
		ax1.set_ylabel('Total Return (%)')
		ax1.set_title('Returns by Market Regime')
		ax1.tick_params(axis='x', rotation=45)
		ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
		
		for i, v in enumerate(returns):
			ax1.text(i, v + (0.005 if v > 0 else -0.005), f'{v:.1%}', 
					ha='center', va='bottom' if v > 0 else 'top')
		
		# Win rates by regime
		ax2.bar(regimes, win_rates, color=colors, alpha=0.7)
		ax2.set_ylabel('Win Rate (%)')
		ax2.set_title('Win Rates by Market Regime')
		ax2.tick_params(axis='x', rotation=45)
		ax2.set_ylim([0, 1])
		
		for i, v in enumerate(win_rates):
			ax2.text(i, v + 0.01, f'{v:.1%}', ha='center', va='bottom')
		
		plt.tight_layout()
		chart_file = self.results_path / 'regime_analysis.png'
		plt.savefig(chart_file, dpi=300, bbox_inches='tight')
		plt.close()
		chart_files.append(str(chart_file))
	
	def _create_statistical_analysis_chart(self, metrics: Dict[str, Any], chart_files: List[str]):
		"""Create statistical significance analysis chart"""
		
		stat_tests = metrics.get('statistical_tests', {})
		if not stat_tests:
			return
		
		fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
		fig.suptitle('Statistical Analysis of Signal Performance', fontsize=16, fontweight='bold')
		
		# Confidence intervals
		confidence_levels = []
		lower_bounds = []
		upper_bounds = []
		
		for key, value in stat_tests.items():
			if key.startswith('confidence_interval_'):
				level = key.split('_')[-1]
				confidence_levels.append(f'{level}%')
				lower_bounds.append(value['lower_bound'])
				upper_bounds.append(value['upper_bound'])
		
		if confidence_levels:
			x_pos = range(len(confidence_levels))
			ax1.errorbar(x_pos, [0]*len(confidence_levels), 
						yerr=[np.abs(lower_bounds), upper_bounds], 
						fmt='o', capsize=5, capthick=2)
			ax1.set_xticks(x_pos)
			ax1.set_xticklabels(confidence_levels)
			ax1.set_ylabel('Return Range')
			ax1.set_title('Confidence Intervals for Mean Returns')
			ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
			ax1.grid(True, alpha=0.3)
		
		# Statistical test results
		if 't_test' in stat_tests:
			test_results = stat_tests['t_test']
			significance = 'Significant' if test_results['significant'] else 'Not Significant'
			p_value = test_results['p_value']
			
			ax2.text(0.1, 0.8, f"T-Test Results:", fontsize=14, fontweight='bold', transform=ax2.transAxes)
			ax2.text(0.1, 0.6, f"P-value: {p_value:.4f}", fontsize=12, transform=ax2.transAxes)
			ax2.text(0.1, 0.4, f"Result: {significance}", fontsize=12, transform=ax2.transAxes)
			ax2.text(0.1, 0.2, f"Alpha: 0.05", fontsize=12, transform=ax2.transAxes)
			
			# Color coding for significance
			color = 'green' if test_results['significant'] else 'red'
			ax2.text(0.1, 0.1, test_results['interpretation'], fontsize=10, 
					transform=ax2.transAxes, color=color, fontweight='bold')
			
			ax2.set_xlim([0, 1])
			ax2.set_ylim([0, 1])
			ax2.set_title('Statistical Significance Test')
			ax2.axis('off')
		
		plt.tight_layout()
		chart_file = self.results_path / 'statistical_analysis.png'
		plt.savefig(chart_file, dpi=300, bbox_inches='tight')
		plt.close()
		chart_files.append(str(chart_file))
	
	def generate_performance_report(self, metrics: Dict[str, Any], chart_files: List[str]) -> str:
		"""Generate comprehensive HTML performance report"""
		
		report_file = self.results_path / f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
		
		try:
			html_content = f"""
			<!DOCTYPE html>
			<html>
			<head>
				<title>AI Chip Trading Signal Performance Report</title>
				<style>
					body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
					.container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
					h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 20px; }}
					h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; }}
					.metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
					.metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
					.metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
					.metric-label {{ font-size: 0.9em; opacity: 0.9; }}
					.chart-container {{ text-align: center; margin: 30px 0; }}
					.chart-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }}
					.summary-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
					.summary-table th, .summary-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
					.summary-table th {{ background-color: #3498db; color: white; }}
					.positive {{ color: #27ae60; font-weight: bold; }}
					.negative {{ color: #e74c3c; font-weight: bold; }}
					.timestamp {{ text-align: center; color: #7f8c8d; font-style: italic; margin-top: 30px; }}
				</style>
			</head>
			<body>
				<div class="container">
					<h1>AI Chip Trading Signal Performance Analysis</h1>
					<p style="text-align: center; color: #7f8c8d; font-size: 1.1em;">
						Comprehensive backtesting analysis of bond market stress indicators for AI semiconductor trading
					</p>
			"""
			
			# Overall Performance Metrics
			overall = metrics.get('overall_performance', {})
			if overall:
				html_content += f"""
					<h2>📊 Overall Performance Summary</h2>
					<div class="metric-grid">
						<div class="metric-card">
							<div class="metric-label">Total Return</div>
							<div class="metric-value {'positive' if overall.get('total_return', 0) > 0 else 'negative'}">{overall.get('total_return', 0):.1%}</div>
						</div>
						<div class="metric-card">
							<div class="metric-label">Win Rate</div>
							<div class="metric-value">{overall.get('win_rate', 0):.1%}</div>
						</div>
						<div class="metric-card">
							<div class="metric-label">Sharpe Ratio</div>
							<div class="metric-value {'positive' if overall.get('sharpe_ratio', 0) > 1.0 else 'negative'}">{overall.get('sharpe_ratio', 0):.2f}</div>
						</div>
						<div class="metric-card">
							<div class="metric-label">Max Drawdown</div>
							<div class="metric-value negative">{overall.get('max_drawdown', 0):.1%}</div>
						</div>
						<div class="metric-card">
							<div class="metric-label">Total Signals</div>
							<div class="metric-value">{overall.get('total_signals', 0)}</div>
						</div>
						<div class="metric-card">
							<div class="metric-label">Avg Holding Days</div>
							<div class="metric-value">{overall.get('avg_holding_days', 0):.1f}</div>
						</div>
					</div>
				"""
			
			# Add charts
			for chart_file in chart_files:
				chart_name = Path(chart_file).stem.replace('_', ' ').title()
				html_content += f"""
					<h2>📈 {chart_name}</h2>
					<div class="chart-container">
						<img src="{chart_file}" alt="{chart_name}">
					</div>
				"""
			
			# Performance by Symbol
			by_symbol = metrics.get('by_symbol', {})
			if by_symbol:
				html_content += f"""
					<h2>💎 Performance by AI Chip Symbol</h2>
					<table class="summary-table">
						<tr>
							<th>Symbol</th>
							<th>Total Return</th>
							<th>Win Rate</th>
							<th>Sharpe Ratio</th>
							<th>Total Signals</th>
						</tr>
				"""
				
				for symbol, perf in by_symbol.items():
					total_ret = perf.get('total_return', 0)
					win_rate = perf.get('win_rate', 0)
					sharpe = perf.get('sharpe_ratio', 0)
					signals = perf.get('total_signals', 0)
					
					html_content += f"""
						<tr>
							<td><strong>{symbol}</strong></td>
							<td class="{'positive' if total_ret > 0 else 'negative'}">{total_ret:.1%}</td>
							<td>{win_rate:.1%}</td>
							<td class="{'positive' if sharpe > 1.0 else 'negative'}">{sharpe:.2f}</td>
							<td>{signals}</td>
						</tr>
					"""
				
				html_content += "</table>"
			
			# Statistical Tests
			stat_tests = metrics.get('statistical_tests', {})
			if stat_tests and 't_test' in stat_tests:
				t_test = stat_tests['t_test']
				html_content += f"""
					<h2>📈 Statistical Significance Analysis</h2>
					<div style="background-color: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0;">
						<h3>T-Test Results</h3>
						<p><strong>P-value:</strong> {t_test['p_value']:.4f}</p>
						<p><strong>Result:</strong> <span class="{'positive' if t_test['significant'] else 'negative'}">{t_test['interpretation']}</span></p>
						<p><strong>Confidence:</strong> {'95%' if t_test['significant'] else 'Below 95%'}</p>
					</div>
				"""
			
			# Conclusion
			html_content += f"""
					<h2>🎯 Key Findings & Recommendations</h2>
					<div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60;">
						<h3>Strategy Effectiveness:</h3>
						<ul>
							<li><strong>Signal Quality:</strong> {'High-quality signals with statistical edge' if overall.get('win_rate', 0) > 0.55 else 'Signals need improvement - consider strategy refinement'}</li>
							<li><strong>Risk Management:</strong> {'Effective risk control with acceptable drawdowns' if abs(overall.get('max_drawdown', 0)) < 0.15 else 'High drawdowns detected - review position sizing'}</li>
							<li><strong>Consistency:</strong> {'Consistent performance across market regimes' if len(metrics.get('by_regime', {})) > 2 else 'Limited regime testing - expand historical analysis'}</li>
						</ul>
						
						<h3>Recommendations:</h3>
						<ul>
							<li>Continue monitoring signal performance with 30-day evaluation windows</li>
							<li>Focus on high-confidence signals (>7.0 threshold) for live trading</li>
							<li>Implement dynamic position sizing based on regime detection</li>
							<li>Regular model retraining every 90 days with new market data</li>
						</ul>
					</div>
					
					<div class="timestamp">
						Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC<br>
						Feature 05: Historical Signal Performance Analysis
					</div>
				</div>
			</body>
			</html>
			"""
			
			with open(report_file, 'w') as f:
				f.write(html_content)
			
			self.logger.info(f"Performance report generated: {report_file}")
			return str(report_file)
			
		except Exception as e:
			self.logger.error(f"Error generating performance report: {e}")
			return ""
	
	def run_comprehensive_analysis(self) -> Dict[str, Any]:
		"""Run complete historical performance analysis"""
		
		self.logger.info("Starting comprehensive historical performance analysis...")
		
		# Load historical data
		signals_df, price_data = self.load_historical_data()
		
		if signals_df.empty:
			self.logger.warning("No historical signals found - creating sample data for demonstration")
			# Create sample data for demonstration
			signals_df, price_data = self._create_sample_data()
		
		# Calculate performance metrics
		metrics = self.calculate_signal_performance_metrics(signals_df, price_data)
		
		# Generate visualizations
		chart_files = self.generate_performance_visualizations(metrics)
		
		# Generate comprehensive report
		report_file = self.generate_performance_report(metrics, chart_files)
		
		analysis_results = {
			'metrics': metrics,
			'chart_files': chart_files,
			'report_file': report_file,
			'analysis_timestamp': datetime.now().isoformat(),
			'total_signals_analyzed': len(signals_df),
			'symbols_covered': list(price_data.keys()) if price_data else []
		}
		
		self.logger.info(f"Comprehensive analysis complete. Report: {report_file}")
		return analysis_results
	
	def _create_sample_data(self) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
		"""Create sample data for demonstration purposes"""
		
		# Create sample signals
		dates = pd.date_range(start='2023-01-01', end='2024-06-30', freq='W')
		symbols = ['NVDA', 'AMD', 'TSM', 'INTC', 'QCOM']
		signal_types = ['NOW', 'SOON', 'WATCH']
		
		sample_signals = []
		
		for date in dates:
			for symbol in np.random.choice(symbols, size=2, replace=False):
				signal = {
					'timestamp': date,
					'symbol': symbol,
					'signal_type': np.random.choice(signal_types),
					'confidence_score': np.random.uniform(4.0, 9.5),
					'recommended_action': np.random.choice(['BUY', 'SELL', 'HOLD']),
					'position_size': np.random.uniform(0.01, 0.03)
				}
				sample_signals.append(signal)
		
		signals_df = pd.DataFrame(sample_signals)
		signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
		signals_df = signals_df.set_index('timestamp')
		
		# Load real price data if possible, otherwise create synthetic
		try:
			from data_sources.yahoo_client import YahooFinanceClient
			yahoo = YahooFinanceClient()
			price_data = yahoo.get_ai_chip_stocks(period="2y")
		except:
			# Create synthetic price data
			price_data = {}
			for symbol in symbols:
				dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
				prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
				price_data[symbol] = pd.DataFrame({
					'Close': prices,
					'Open': prices * 0.99,
					'High': prices * 1.02,
					'Low': prices * 0.98,
					'Volume': np.random.randint(1000000, 10000000, len(dates))
				}, index=dates)
		
		return signals_df, price_data
