import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from signals.bond_stress_analyzer import BondStressSignal, SignalStrength

@dataclass
class ChipTradingSignal:
	"""AI chip trading signal data structure"""
	timestamp: datetime
	symbol: str
	signal_type: str  # "BUY", "SELL", "HOLD"
	signal_strength: SignalStrength
	confidence_score: float
	target_horizon_days: int
	bond_correlation: float
	suggested_position_size: float  # Percentage of portfolio
	entry_price: float
	stop_loss: float
	take_profit: float
	reasoning: str

class CorrelationEngine:
	"""Translates bond market stress into AI chip trading signals"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.ai_chip_symbols = ['NVDA', 'AMD', 'TSM', 'INTC', 'QCOM']
		
	def calculate_bond_chip_correlation(self, 
		bond_stress_data: pd.Series, 
		chip_returns: pd.Series, 
		window: int = 60
	) -> float:
		"""Calculate rolling correlation between bond stress and chip returns"""
		try:
			# Align data by date
			aligned_data = pd.DataFrame({
				'bond_stress': bond_stress_data,
				'chip_returns': chip_returns
			}).dropna()
			
			if len(aligned_data) < window:
				self.logger.warning(f"Insufficient data for correlation: {len(aligned_data)} < {window}")
				return 0.0
			
			correlation = aligned_data['bond_stress'].rolling(window=window).corr(
				aligned_data['chip_returns']
			).iloc[-1]
			
			return correlation if not np.isnan(correlation) else 0.0
			
		except Exception as e:
			self.logger.error(f"Error calculating correlation: {e}")
			return 0.0
	
	def calculate_momentum_indicators(self, price_data: pd.Series, periods: List[int] = [5, 10, 20]) -> Dict[str, float]:
		"""Calculate momentum indicators for trend analysis"""
		try:
			momentum = {}
			current_price = price_data.iloc[-1]
			
			for period in periods:
				if len(price_data) >= period:
					past_price = price_data.iloc[-period]
					momentum[f'{period}d_return'] = (current_price - past_price) / past_price
				else:
					momentum[f'{period}d_return'] = 0.0
			
			# RSI-like momentum
			if len(price_data) >= 14:
				returns = price_data.pct_change().dropna()
				gains = returns.where(returns > 0, 0)
				losses = -returns.where(returns < 0, 0)
				
				avg_gain = gains.rolling(14).mean().iloc[-1]
				avg_loss = losses.rolling(14).mean().iloc[-1]
				
				if avg_loss != 0:
					rs = avg_gain / avg_loss
					rsi = 100 - (100 / (1 + rs))
					momentum['rsi'] = rsi
				else:
					momentum['rsi'] = 50.0
			else:
				momentum['rsi'] = 50.0
			
			return momentum
			
		except Exception as e:
			self.logger.error(f"Error calculating momentum: {e}")
			return {f'{p}d_return': 0.0 for p in periods}
	
	def generate_chip_trading_signals(self, 
		bond_signal: BondStressSignal,
		chip_prices: Dict[str, pd.DataFrame],
		yield_curve_data: pd.Series
	) -> List[ChipTradingSignal]:
		"""Generate AI chip trading signals based on bond stress"""
		
		signals = []
		
		for symbol in self.ai_chip_symbols:
			try:
				if symbol not in chip_prices or chip_prices[symbol].empty:
					self.logger.warning(f"No price data for {symbol}")
					continue
				
				price_data = chip_prices[symbol]['Close']
				current_price = price_data.iloc[-1]
				
				# Calculate correlations and momentum
				chip_returns = price_data.pct_change().dropna()
				correlation = self.calculate_bond_chip_correlation(
					yield_curve_data, chip_returns
				)
				
				momentum = self.calculate_momentum_indicators(price_data)
				
				# Generate signal based on bond stress and correlations
				signal_type, confidence, horizon, position_size, reasoning = self._determine_trading_action(
					bond_signal, correlation, momentum, symbol
				)
				
				# Calculate risk management levels
				stop_loss, take_profit = self._calculate_risk_levels(
					current_price, signal_type, momentum['20d_return']
				)
				
				chip_signal = ChipTradingSignal(
					timestamp=datetime.now(),
					symbol=symbol,
					signal_type=signal_type,
					signal_strength=bond_signal.signal_strength,
					confidence_score=confidence,
					target_horizon_days=horizon,
					bond_correlation=correlation,
					suggested_position_size=position_size,
					entry_price=current_price,
					stop_loss=stop_loss,
					take_profit=take_profit,
					reasoning=reasoning
				)
				
				signals.append(chip_signal)
				
			except Exception as e:
				self.logger.error(f"Error generating signal for {symbol}: {e}")
				continue
		
		return signals
	
	def _determine_trading_action(self, 
		bond_signal: BondStressSignal,
		correlation: float,
		momentum: Dict[str, float],
		symbol: str
	) -> Tuple[str, float, int, float, str]:
		"""Determine trading action based on bond stress and correlations"""
		
		base_confidence = bond_signal.confidence_score
		reasoning_parts = []
		
		# Bond stress interpretation
		if bond_signal.signal_strength == SignalStrength.NOW:
			if correlation < -0.3:  # Strong negative correlation with bond stress
				signal_type = "BUY"
				reasoning_parts.append("Strong bond stress + negative correlation")
				confidence_boost = 2.0
			elif correlation > 0.3:  # Positive correlation - avoid
				signal_type = "SELL"
				reasoning_parts.append("Bond stress + positive correlation")
				confidence_boost = 1.5
			else:
				signal_type = "HOLD"
				reasoning_parts.append("Bond stress but unclear correlation")
				confidence_boost = 0.5
				
		elif bond_signal.signal_strength == SignalStrength.SOON:
			if correlation < -0.2:
				signal_type = "BUY"
				reasoning_parts.append("Moderate bond stress + negative correlation")
				confidence_boost = 1.5
			else:
				signal_type = "WATCH"
				reasoning_parts.append("Moderate bond stress - monitoring")
				confidence_boost = 1.0
				
		else:  # WATCH or NEUTRAL
			signal_type = "HOLD"
			reasoning_parts.append("Low bond stress")
			confidence_boost = 0.5
		
		# Momentum overlay
		if momentum['5d_return'] > 0.03 and momentum['20d_return'] > 0.1:
			if signal_type == "BUY":
				reasoning_parts.append("Strong upward momentum")
				confidence_boost += 1.0
			elif signal_type == "SELL":
				confidence_boost -= 0.5  # Reduce confidence in sell signal
				
		elif momentum['5d_return'] < -0.03 and momentum['20d_return'] < -0.1:
			if signal_type == "SELL":
				reasoning_parts.append("Strong downward momentum")
				confidence_boost += 1.0
			elif signal_type == "BUY":
				confidence_boost -= 0.5  # Reduce confidence in buy signal
		
		# RSI overlay
		if momentum['rsi'] > 70 and signal_type == "BUY":
			confidence_boost -= 1.0
			reasoning_parts.append("Overbought condition")
		elif momentum['rsi'] < 30 and signal_type == "SELL":
			confidence_boost -= 1.0
			reasoning_parts.append("Oversold condition")
		
		# Final confidence and position sizing
		final_confidence = min(10.0, max(1.0, base_confidence + confidence_boost))
		
		# Position sizing based on confidence and signal strength
		if signal_type in ["BUY", "SELL"]:
			base_position = 0.1  # 10% base position
			confidence_multiplier = final_confidence / 10.0
			signal_multiplier = {
				SignalStrength.NOW: 1.5,
				SignalStrength.SOON: 1.0,
				SignalStrength.WATCH: 0.5
			}.get(bond_signal.signal_strength, 0.5)
			
			position_size = min(0.25, base_position * confidence_multiplier * signal_multiplier)
		else:
			position_size = 0.0
		
		# Time horizon based on signal strength
		horizon_map = {
			SignalStrength.NOW: 7,      # 1 week for immediate signals
			SignalStrength.SOON: 21,    # 3 weeks for developing signals
			SignalStrength.WATCH: 42,   # 6 weeks for watch signals
			SignalStrength.NEUTRAL: 60  # 2 months for neutral
		}
		horizon = horizon_map.get(bond_signal.signal_strength, 30)
		
		reasoning = f"{symbol}: {' + '.join(reasoning_parts)}"
		
		return signal_type, final_confidence, horizon, position_size, reasoning
	
	def _calculate_risk_levels(self, current_price: float, signal_type: str, momentum: float) -> Tuple[float, float]:
		"""Calculate stop loss and take profit levels"""
		
		if signal_type == "BUY":
			# Stop loss: 3-5% below entry based on volatility
			base_stop = 0.03 if abs(momentum) < 0.05 else 0.05
			stop_loss = current_price * (1 - base_stop)
			
			# Take profit: 2:1 risk reward ratio
			profit_target = base_stop * 2
			take_profit = current_price * (1 + profit_target)
			
		elif signal_type == "SELL":
			# For short positions (if allowed)
			base_stop = 0.03 if abs(momentum) < 0.05 else 0.05
			stop_loss = current_price * (1 + base_stop)
			
			profit_target = base_stop * 2
			take_profit = current_price * (1 - profit_target)
			
		else:
			stop_loss = current_price * 0.95  # Default 5% stop
			take_profit = current_price * 1.1  # Default 10% target
		
		return stop_loss, take_profit
