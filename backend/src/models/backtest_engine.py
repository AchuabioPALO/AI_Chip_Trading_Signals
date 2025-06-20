import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')

@dataclass
class BacktestResults:
	"""Results from backtesting analysis"""
	total_return: float
	annual_return: float
	volatility: float
	sharpe_ratio: float
	max_drawdown: float
	win_rate: float
	total_trades: int
	avg_holding_days: float
	best_trade: float
	worst_trade: float
	profit_factor: float

class BacktestEngine:
	"""Comprehensive backtesting framework for bond-chip trading signals"""
	
	def __init__(self, initial_capital: float = 100000):
		self.logger = logging.getLogger(__name__)
		self.initial_capital = initial_capital
		self.transaction_cost = 0.001  # 0.1% transaction costs
		
	def run_historical_backtest(self, 
		signals_df: pd.DataFrame,
		price_data: Dict[str, pd.DataFrame],
		start_date: str = "2020-01-01",
		end_date: str = "2024-12-31"
	) -> BacktestResults:
		"""Run comprehensive historical backtest"""
		
		try:
			# Filter data by date range
			start_dt = pd.to_datetime(start_date)
			end_dt = pd.to_datetime(end_date)
			
			signals_filtered = signals_df[
				(signals_df.index >= start_dt) & 
				(signals_df.index <= end_dt)
			].copy()
			
			if signals_filtered.empty:
				self.logger.warning("No signals in specified date range")
				return self._empty_results()
			
			# Initialize portfolio tracking
			portfolio = pd.DataFrame(index=signals_filtered.index)
			portfolio['cash'] = self.initial_capital
			portfolio['portfolio_value'] = self.initial_capital
			portfolio['positions'] = 0.0
			portfolio['signal_strength'] = signals_filtered.get('signal_strength', 1.0)
			
			trades = []
			current_position = 0.0
			current_symbol = None
			entry_price = 0.0
			entry_date = None
			
			for date, signal_row in signals_filtered.iterrows():
				# Get current market prices
				current_prices = self._get_current_prices(date, price_data)
				
				if not current_prices:
					continue
				
				# Determine action based on signal
				action, symbol, position_size = self._parse_signal(signal_row)
				
				if action == "BUY" and current_position <= 0:
					# Open long position
					if symbol in current_prices:
						price = current_prices[symbol]
						shares = (self.initial_capital * position_size) / price
						shares = shares * (1 - self.transaction_cost)  # Apply transaction costs
						
						current_position = shares
						current_symbol = symbol
						entry_price = price
						entry_date = date
						
						portfolio.loc[date, 'positions'] = shares * price
						portfolio.loc[date, 'cash'] = self.initial_capital - (shares * price)
						
				elif action == "SELL" and current_position > 0:
					# Close long position
					if current_symbol in current_prices:
						exit_price = current_prices[current_symbol]
						exit_value = current_position * exit_price * (1 - self.transaction_cost)
						
						# Record trade
						trade_return = (exit_price - entry_price) / entry_price
						holding_days = (date - entry_date).days if entry_date else 0
						
						trades.append({
							'entry_date': entry_date,
							'exit_date': date,
							'symbol': current_symbol,
							'entry_price': entry_price,
							'exit_price': exit_price,
							'return': trade_return,
							'holding_days': holding_days,
							'pnl': exit_value - (current_position * entry_price)
						})
						
						# Reset position
						portfolio.loc[date, 'cash'] = self.initial_capital + (exit_value - self.initial_capital)
						portfolio.loc[date, 'positions'] = 0.0
						current_position = 0.0
						current_symbol = None
				
				# Update portfolio value
				if current_position > 0 and current_symbol in current_prices:
					portfolio.loc[date, 'positions'] = current_position * current_prices[current_symbol]
				
				portfolio.loc[date, 'portfolio_value'] = (
					portfolio.loc[date, 'cash'] + portfolio.loc[date, 'positions']
				)
			
			# Calculate performance metrics
			results = self._calculate_performance_metrics(portfolio, trades)
			
			self.logger.info(f"Backtest completed: {results.total_trades} trades, "
							f"{results.annual_return:.1%} annual return, "
							f"{results.sharpe_ratio:.2f} Sharpe ratio")
			
			return results
			
		except Exception as e:
			self.logger.error(f"Error running backtest: {e}")
			return self._empty_results()
	
	def walk_forward_analysis(self, 
		signals_df: pd.DataFrame,
		price_data: Dict[str, pd.DataFrame],
		train_window: int = 252,  # 1 year
		test_window: int = 63     # 3 months
	) -> Dict[str, List]:
		"""Perform walk-forward analysis to avoid overfitting"""
		
		try:
			results = {
				'period_returns': [],
				'sharpe_ratios': [],
				'max_drawdowns': [],
				'win_rates': [],
				'dates': []
			}
			
			start_idx = train_window
			end_idx = len(signals_df) - test_window
			
			for i in range(start_idx, end_idx, test_window):
				# Define train and test periods
				train_start = signals_df.index[i - train_window]
				train_end = signals_df.index[i - 1]
				test_start = signals_df.index[i]
				test_end = signals_df.index[min(i + test_window - 1, len(signals_df) - 1)]
				
				# Run backtest on test period
				test_signals = signals_df[test_start:test_end]
				
				if test_signals.empty:
					continue
				
				backtest_result = self.run_historical_backtest(
					test_signals, 
					price_data,
					test_start.strftime('%Y-%m-%d'),
					test_end.strftime('%Y-%m-%d')
				)
				
				# Store results
				results['period_returns'].append(backtest_result.annual_return)
				results['sharpe_ratios'].append(backtest_result.sharpe_ratio)
				results['max_drawdowns'].append(backtest_result.max_drawdown)
				results['win_rates'].append(backtest_result.win_rate)
				results['dates'].append(test_end)
			
			self.logger.info(f"Walk-forward analysis completed: {len(results['dates'])} periods")
			
			return results
			
		except Exception as e:
			self.logger.error(f"Error in walk-forward analysis: {e}")
			return {}
	
	def analyze_signal_quality(self, 
		signals_df: pd.DataFrame,
		price_data: Dict[str, pd.DataFrame],
		forward_returns_days: List[int] = [5, 10, 20, 60]
	) -> pd.DataFrame:
		"""Analyze signal quality by looking at forward returns"""
		
		try:
			signal_analysis = signals_df.copy()
			
			# Calculate forward returns for each horizon
			for symbol in ['NVDA', 'AMD', 'TSM']:  # Main AI chip stocks
				if symbol not in price_data:
					continue
				
				prices = price_data[symbol]['Close']
				
				for days in forward_returns_days:
					forward_returns = prices.shift(-days) / prices - 1
					signal_analysis[f'{symbol}_fwd_{days}d'] = forward_returns
			
			# Analyze signal effectiveness
			signal_effectiveness = {}
			
			for signal_strength in ['NOW', 'SOON', 'WATCH']:
				mask = signal_analysis['signal_strength'] == signal_strength
				subset = signal_analysis[mask]
				
				if subset.empty:
					continue
				
				effectiveness = {}
				for col in subset.columns:
					if '_fwd_' in col and 'd' in col:
						returns = subset[col].dropna()
						if len(returns) > 0:
							effectiveness[col] = {
								'mean_return': returns.mean(),
								'hit_rate': (returns > 0).mean(),
								'std_return': returns.std(),
								'sample_size': len(returns)
							}
				
				signal_effectiveness[signal_strength] = effectiveness
			
			return pd.DataFrame(signal_effectiveness).T
			
		except Exception as e:
			self.logger.error(f"Error analyzing signal quality: {e}")
			return pd.DataFrame()
	
	def _get_current_prices(self, date: pd.Timestamp, price_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
		"""Get current market prices for all symbols"""
		prices = {}
		
		for symbol, data in price_data.items():
			try:
				# Find the closest available price
				available_dates = data.index[data.index <= date]
				if len(available_dates) > 0:
					latest_date = available_dates[-1]
					prices[symbol] = data.loc[latest_date, 'Close']
			except:
				continue
				
		return prices
	
	def _parse_signal(self, signal_row: pd.Series) -> Tuple[str, str, float]:
		"""Parse signal row to determine action"""
		
		# Default values
		action = "HOLD"
		symbol = "NVDA"  # Default to NVIDIA
		position_size = 0.0
		
		try:
			signal_strength = signal_row.get('signal_strength', 'NEUTRAL')
			confidence = signal_row.get('confidence_score', 5.0)
			
			# Determine action based on signal strength
			if signal_strength in ['NOW', 'SOON']:
				action = "BUY"
				# Position size based on confidence (5-25% of portfolio)
				position_size = min(0.25, max(0.05, confidence / 40.0))
			elif signal_strength == 'WATCH':
				action = "HOLD"
			else:
				action = "SELL"
				position_size = 0.0
			
			# Symbol selection (can be enhanced)
			if 'symbol' in signal_row:
				symbol = signal_row['symbol']
			
		except Exception as e:
			self.logger.error(f"Error parsing signal: {e}")
		
		return action, symbol, position_size
	
	def _calculate_performance_metrics(self, portfolio: pd.DataFrame, trades: List[Dict]) -> BacktestResults:
		"""Calculate comprehensive performance metrics"""
		
		try:
			if portfolio.empty or not trades:
				return self._empty_results()
			
			# Portfolio returns
			portfolio_values = portfolio['portfolio_value'].dropna()
			returns = portfolio_values.pct_change().dropna()
			
			# Basic metrics
			total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
			days = (portfolio.index[-1] - portfolio.index[0]).days
			annual_return = (1 + total_return) ** (365.25 / days) - 1
			volatility = returns.std() * np.sqrt(252)
			
			# Sharpe ratio (assuming 2% risk-free rate)
			risk_free_rate = 0.02
			sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
			
			# Maximum drawdown
			peak = portfolio_values.expanding().max()
			drawdown = (portfolio_values - peak) / peak
			max_drawdown = drawdown.min()
			
			# Trade statistics
			trade_returns = [trade['return'] for trade in trades]
			win_rate = sum(1 for ret in trade_returns if ret > 0) / len(trade_returns) if trade_returns else 0
			avg_holding_days = np.mean([trade['holding_days'] for trade in trades]) if trades else 0
			
			best_trade = max(trade_returns) if trade_returns else 0
			worst_trade = min(trade_returns) if trade_returns else 0
			
			# Profit factor
			gross_profit = sum(ret for ret in trade_returns if ret > 0)
			gross_loss = abs(sum(ret for ret in trade_returns if ret < 0))
			profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
			
			return BacktestResults(
				total_return=total_return,
				annual_return=annual_return,
				volatility=volatility,
				sharpe_ratio=sharpe_ratio,
				max_drawdown=max_drawdown,
				win_rate=win_rate,
				total_trades=len(trades),
				avg_holding_days=avg_holding_days,
				best_trade=best_trade,
				worst_trade=worst_trade,
				profit_factor=profit_factor
			)
			
		except Exception as e:
			self.logger.error(f"Error calculating metrics: {e}")
			return self._empty_results()
	
	def _empty_results(self) -> BacktestResults:
		"""Return empty results for error cases"""
		return BacktestResults(
			total_return=0.0,
			annual_return=0.0,
			volatility=0.0,
			sharpe_ratio=0.0,
			max_drawdown=0.0,
			win_rate=0.0,
			total_trades=0,
			avg_holding_days=0.0,
			best_trade=0.0,
			worst_trade=0.0,
			profit_factor=0.0
		)
	
	def plot_backtest_results(self, portfolio: pd.DataFrame, title: str = "Portfolio Performance"):
		"""Create performance visualization"""
		
		try:
			fig, axes = plt.subplots(2, 2, figsize=(15, 10))
			fig.suptitle(title, fontsize=16)
			
			# Portfolio value over time
			axes[0, 0].plot(portfolio.index, portfolio['portfolio_value'])
			axes[0, 0].set_title('Portfolio Value')
			axes[0, 0].set_ylabel('Value ($)')
			
			# Returns distribution
			returns = portfolio['portfolio_value'].pct_change().dropna()
			axes[0, 1].hist(returns, bins=50, alpha=0.7)
			axes[0, 1].set_title('Returns Distribution')
			axes[0, 1].set_xlabel('Daily Returns')
			
			# Drawdown
			peak = portfolio['portfolio_value'].expanding().max()
			drawdown = (portfolio['portfolio_value'] - peak) / peak
			axes[1, 0].fill_between(portfolio.index, drawdown, 0, alpha=0.3, color='red')
			axes[1, 0].set_title('Drawdown')
			axes[1, 0].set_ylabel('Drawdown %')
			
			# Rolling Sharpe ratio
			rolling_sharpe = returns.rolling(60).mean() / returns.rolling(60).std() * np.sqrt(252)
			axes[1, 1].plot(portfolio.index[60:], rolling_sharpe[60:])
			axes[1, 1].set_title('Rolling 60-Day Sharpe Ratio')
			axes[1, 1].axhline(y=0, color='r', linestyle='--')
			
			plt.tight_layout()
			plt.show()
			
		except Exception as e:
			self.logger.error(f"Error plotting results: {e}")
