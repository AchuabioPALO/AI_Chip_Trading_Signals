import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import os
from signals.bond_stress_analyzer import BondStressSignal, SignalStrength
from signals.correlation_engine import ChipTradingSignal

class NotificationSystem:
	"""Unified notification system for trading signals"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		
		# Configuration from environment
		self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
		self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
		self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
		self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
		
		# Notification thresholds
		self.min_confidence_threshold = 6.0
		self.signal_strength_priority = {
			SignalStrength.NOW: 1,
			SignalStrength.SOON: 2,
			SignalStrength.WATCH: 3,
			SignalStrength.NEUTRAL: 4
		}
		
	async def send_bond_stress_alert(self, signal: BondStressSignal):
		"""Send bond stress alert to all configured channels"""
		
		if signal.confidence_score < self.min_confidence_threshold:
			self.logger.debug(f"Signal confidence {signal.confidence_score} below threshold")
			return
		
		# Format message
		message = self._format_bond_stress_message(signal)
		
		# Send to all channels
		tasks = []
		
		if self.slack_webhook:
			tasks.append(self._send_slack_message(message, signal))
		
		if self.telegram_token and self.telegram_chat_id:
			tasks.append(self._send_telegram_message(message, signal))
		
		if self.discord_webhook:
			tasks.append(self._send_discord_message(message, signal))
		
		if tasks:
			await asyncio.gather(*tasks, return_exceptions=True)
			self.logger.info(f"Bond stress alert sent: {signal.signal_strength.value}")
	
	async def send_chip_trading_alerts(self, signals: List[ChipTradingSignal]):
		"""Send AI chip trading alerts"""
		
		# Filter high-priority signals
		priority_signals = [
			signal for signal in signals
			if signal.confidence_score >= self.min_confidence_threshold
			and signal.signal_type in ['BUY', 'SELL']
		]
		
		if not priority_signals:
			return
		
		# Sort by priority and confidence
		priority_signals.sort(
			key=lambda s: (
				self.signal_strength_priority.get(s.signal_strength, 5),
				-s.confidence_score
			)
		)
		
		# Take top 3 signals to avoid spam
		top_signals = priority_signals[:3]
		
		for signal in top_signals:
			message = self._format_chip_signal_message(signal)
			
			tasks = []
			
			if self.slack_webhook:
				tasks.append(self._send_slack_message(message, signal, is_chip_signal=True))
			
			if self.telegram_token and self.telegram_chat_id:
				tasks.append(self._send_telegram_message(message, signal, is_chip_signal=True))
			
			if self.discord_webhook:
				tasks.append(self._send_discord_message(message, signal, is_chip_signal=True))
			
			if tasks:
				await asyncio.gather(*tasks, return_exceptions=True)
		
		self.logger.info(f"Chip trading alerts sent: {len(top_signals)} signals")
	
	def _format_bond_stress_message(self, signal: BondStressSignal) -> str:
		"""Format bond stress signal for notifications"""
		
		emoji_map = {
			SignalStrength.NOW: "🚨",
			SignalStrength.SOON: "⚠️",
			SignalStrength.WATCH: "👀",
			SignalStrength.NEUTRAL: "😐"
		}
		
		emoji = emoji_map.get(signal.signal_strength, "📊")
		
		message = f"""
{emoji} **BOND STRESS ALERT** {emoji}

📈 **Signal Strength:** {signal.signal_strength.value}
🎯 **Confidence:** {signal.confidence_score:.1f}/10
📊 **Yield Curve:** {signal.yield_curve_spread:.2f} bps (Z-score: {signal.yield_curve_zscore:.2f})
📉 **Bond Volatility:** {signal.bond_volatility:.4f}
💡 **Action:** {signal.suggested_action}

⏰ Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
		return message.strip()
	
	def _format_chip_signal_message(self, signal: ChipTradingSignal) -> str:
		"""Format chip trading signal for notifications"""
		
		action_emoji = {
			"BUY": "🟢",
			"SELL": "🔴",
			"HOLD": "🟡",
			"WATCH": "👀"
		}
		
		emoji = action_emoji.get(signal.signal_type, "📊")
		
		message = f"""
{emoji} **AI CHIP SIGNAL** {emoji}

💎 **Symbol:** {signal.symbol}
📈 **Action:** {signal.signal_type}
🎯 **Confidence:** {signal.confidence_score:.1f}/10
💰 **Entry Price:** ${signal.entry_price:.2f}
📊 **Position Size:** {signal.suggested_position_size:.1%}
🔗 **Bond Correlation:** {signal.bond_correlation:.3f}
📅 **Target Horizon:** {signal.target_horizon_days} days

💡 **Reasoning:** {signal.reasoning[:100]}...

⏰ Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
		return message.strip()
	
	async def _send_slack_message(self, message: str, signal, is_chip_signal: bool = False):
		"""Send message to Slack webhook"""
		
		try:
			if not self.slack_webhook:
				return
			
			# Determine color based on signal
			if is_chip_signal:
				color = "#36a64f" if signal.signal_type == "BUY" else "#ff0000" if signal.signal_type == "SELL" else "#ffaa00"
			else:
				color_map = {
					SignalStrength.NOW: "#ff0000",
					SignalStrength.SOON: "#ffaa00",
					SignalStrength.WATCH: "#36a64f",
					SignalStrength.NEUTRAL: "#808080"
				}
				color = color_map.get(signal.signal_strength, "#808080")
			
			payload = {
				"attachments": [
					{
						"color": color,
						"text": message,
						"mrkdwn_in": ["text"]
					}
				]
			}
			
			async with aiohttp.ClientSession() as session:
				async with session.post(self.slack_webhook, json=payload) as response:
					if response.status == 200:
						self.logger.debug("Slack message sent successfully")
					else:
						self.logger.error(f"Slack webhook failed: {response.status}")
		
		except Exception as e:
			self.logger.error(f"Error sending Slack message: {e}")
	
	async def _send_telegram_message(self, message: str, signal, is_chip_signal: bool = False):
		"""Send message to Telegram bot"""
		
		try:
			if not self.telegram_token or not self.telegram_chat_id:
				return
			
			url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
			
			payload = {
				"chat_id": self.telegram_chat_id,
				"text": message,
				"parse_mode": "Markdown"
			}
			
			async with aiohttp.ClientSession() as session:
				async with session.post(url, json=payload) as response:
					if response.status == 200:
						self.logger.debug("Telegram message sent successfully")
					else:
						self.logger.error(f"Telegram API failed: {response.status}")
		
		except Exception as e:
			self.logger.error(f"Error sending Telegram message: {e}")
	
	async def _send_discord_message(self, message: str, signal, is_chip_signal: bool = False):
		"""Send message to Discord webhook"""
		
		try:
			if not self.discord_webhook:
				return
			
			# Discord embed color
			if is_chip_signal:
				color = 0x00ff00 if signal.signal_type == "BUY" else 0xff0000 if signal.signal_type == "SELL" else 0xffaa00
			else:
				color_map = {
					SignalStrength.NOW: 0xff0000,
					SignalStrength.SOON: 0xffaa00,
					SignalStrength.WATCH: 0x00ff00,
					SignalStrength.NEUTRAL: 0x808080
				}
				color = color_map.get(signal.signal_strength, 0x808080)
			
			payload = {
				"embeds": [
					{
						"description": message,
						"color": color,
						"timestamp": datetime.now().isoformat()
					}
				]
			}
			
			async with aiohttp.ClientSession() as session:
				async with session.post(self.discord_webhook, json=payload) as response:
					if response.status in [200, 204]:
						self.logger.debug("Discord message sent successfully")
					else:
						self.logger.error(f"Discord webhook failed: {response.status}")
		
		except Exception as e:
			self.logger.error(f"Error sending Discord message: {e}")
	
	async def send_daily_summary(self, 
		bond_signal: BondStressSignal,
		chip_signals: List[ChipTradingSignal],
		portfolio_value: float = None,
		daily_pnl: float = None
	):
		"""Send daily summary report"""
		
		summary = self._format_daily_summary(bond_signal, chip_signals, portfolio_value, daily_pnl)
		
		tasks = []
		
		if self.slack_webhook:
			tasks.append(self._send_slack_summary(summary))
		
		if self.telegram_token and self.telegram_chat_id:
			tasks.append(self._send_telegram_summary(summary))
		
		if tasks:
			await asyncio.gather(*tasks, return_exceptions=True)
			self.logger.info("Daily summary sent")
	
	def _format_daily_summary(self, 
		bond_signal: BondStressSignal,
		chip_signals: List[ChipTradingSignal],
		portfolio_value: float = None,
		daily_pnl: float = None
	) -> str:
		"""Format daily summary report"""
		
		# Count signals by type
		signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "WATCH": 0}
		high_conf_signals = []
		
		for signal in chip_signals:
			signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
			if signal.confidence_score >= 7.0:
				high_conf_signals.append(f"{signal.symbol}: {signal.signal_type}")
		
		summary = f"""
📊 **DAILY TRADING SUMMARY** 📊
{datetime.now().strftime('%Y-%m-%d')}

🏦 **Bond Market Status:**
• Signal: {bond_signal.signal_strength.value} (Confidence: {bond_signal.confidence_score:.1f})
• Yield Curve: {bond_signal.yield_curve_spread:.2f} bps
• Action: {bond_signal.suggested_action[:50]}...

💎 **AI Chip Signals:**
• BUY: {signal_counts['BUY']} | SELL: {signal_counts['SELL']} | HOLD: {signal_counts['HOLD']}
• High Confidence (>7.0): {len(high_conf_signals)}
"""
		
		if high_conf_signals:
			summary += f"\n🎯 **Top Signals:** {', '.join(high_conf_signals[:3])}"
		
		if portfolio_value:
			summary += f"\n💰 **Portfolio Value:** ${portfolio_value:,.2f}"
		
		if daily_pnl is not None:
			pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
			summary += f"\n{pnl_emoji} **Daily P&L:** ${daily_pnl:+,.2f}"
		
		return summary.strip()
	
	async def _send_slack_summary(self, summary: str):
		"""Send daily summary to Slack"""
		
		payload = {
			"text": "Daily Trading Summary",
			"attachments": [
				{
					"color": "#36a64f",
					"text": summary,
					"mrkdwn_in": ["text"]
				}
			]
		}
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(self.slack_webhook, json=payload) as response:
					if response.status == 200:
						self.logger.debug("Slack summary sent successfully")
		except Exception as e:
			self.logger.error(f"Error sending Slack summary: {e}")
	
	async def _send_telegram_summary(self, summary: str):
		"""Send daily summary to Telegram"""
		
		url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
		payload = {
			"chat_id": self.telegram_chat_id,
			"text": summary,
			"parse_mode": "Markdown"
		}
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(url, json=payload) as response:
					if response.status == 200:
						self.logger.debug("Telegram summary sent successfully")
		except Exception as e:
			self.logger.error(f"Error sending Telegram summary: {e}")
	
	def test_notifications(self) -> Dict[str, bool]:
		"""Test all notification channels"""
		
		results = {}
		
		test_message = "🧪 **Test Message** - AI Chip Trading Signal System is online!"
		
		async def run_tests():
			if self.slack_webhook:
				try:
					payload = {"text": test_message}
					async with aiohttp.ClientSession() as session:
						async with session.post(self.slack_webhook, json=payload) as response:
							results['slack'] = response.status == 200
				except:
					results['slack'] = False
			
			if self.telegram_token and self.telegram_chat_id:
				try:
					url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
					payload = {"chat_id": self.telegram_chat_id, "text": test_message}
					async with aiohttp.ClientSession() as session:
						async with session.post(url, json=payload) as response:
							results['telegram'] = response.status == 200
				except:
					results['telegram'] = False
			
			if self.discord_webhook:
				try:
					payload = {"content": test_message}
					async with aiohttp.ClientSession() as session:
						async with session.post(self.discord_webhook, json=payload) as response:
							results['discord'] = response.status in [200, 204]
				except:
					results['discord'] = False
		
		# Run async tests
		asyncio.run(run_tests())
		
		return results
