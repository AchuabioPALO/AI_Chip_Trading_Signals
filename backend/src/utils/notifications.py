import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from signals.bond_stress_analyzer import BondStressSignal, SignalStrength
from signals.correlation_engine import ChipTradingSignal

class NotificationSystem:
	"""Discord-focused notification system for trading signals"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		
		# Load environment variables from the correct path
		from dotenv import load_dotenv
		load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')
		
		# Discord configuration - primary notification channel
		self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
		
		# Load user preferences
		self.config_file = Path(__file__).parent.parent.parent / 'data' / 'notification_config.json'
		self.user_preferences = self._load_user_preferences()
		
		# Rate limiting to prevent spam
		self.last_sent = {}
		self.min_interval_seconds = self.user_preferences.get('min_interval_seconds', 300)  # 5 minutes default
		
		# Notification queue for simple queuing
		self.notification_queue = []
		self.max_queue_size = 50
		
		# Notification statistics
		self.stats = {
			'total_sent': 0,
			'failed_sends': 0,
			'last_daily_summary': None
		}
		
		# Notification thresholds from config
		self.min_confidence_threshold = self.user_preferences.get('min_confidence_threshold', 6.0)
		self.signal_strength_priority = {
			SignalStrength.NOW: 1,
			SignalStrength.SOON: 2,
			SignalStrength.WATCH: 3,
			SignalStrength.NEUTRAL: 4
		}
		
	def _load_user_preferences(self) -> Dict:
		"""Load notification preferences from JSON config file"""
		default_config = {
			"min_confidence_threshold": 6.0,
			"min_interval_seconds": 300,
			"enabled_notifications": {
				"bond_stress": True,
				"chip_signals": True,
				"daily_summary": True,
				"error_alerts": True
			},
			"discord_settings": {
				"enabled": True,
				"rich_embeds": True,
				"use_mentions": False,
				"mention_role_id": None
			},
			"rate_limiting": {
				"max_per_hour": 12,
				"burst_protection": True
			}
		}
		
		try:
			if self.config_file.exists():
				with open(self.config_file, 'r') as f:
					config = json.load(f)
					# Merge with defaults
					default_config.update(config)
			else:
				# Create default config file
				self.config_file.parent.mkdir(parents=True, exist_ok=True)
				with open(self.config_file, 'w') as f:
					json.dump(default_config, f, indent=2)
				self.logger.info(f"Created default notification config: {self.config_file}")
		except Exception as e:
			self.logger.error(f"Error loading notification config: {e}")
		
		return default_config
	
	def _should_send_notification(self, signal_type: str, signal_id: str = None) -> bool:
		"""Check if notification should be sent based on rate limiting"""
		now = datetime.now()
		
		# Check if notification type is enabled
		if not self.user_preferences.get('enabled_notifications', {}).get(signal_type, True):
			return False
		
		# Rate limiting key
		rate_key = f"{signal_type}_{signal_id}" if signal_id else signal_type
		
		# Check minimum interval
		if rate_key in self.last_sent:
			time_since_last = (now - self.last_sent[rate_key]).total_seconds()
			if time_since_last < self.min_interval_seconds:
				self.logger.debug(f"Rate limited: {rate_key} sent {time_since_last:.0f}s ago")
				return False
		
		# Check hourly rate limit
		rate_config = self.user_preferences.get('rate_limiting', {})
		max_per_hour = rate_config.get('max_per_hour', 12)
		
		# Count notifications in last hour
		hour_ago = now - timedelta(hours=1)
		recent_sends = [ts for ts in self.last_sent.values() if ts > hour_ago]
		
		if len(recent_sends) >= max_per_hour:
			self.logger.warning(f"Hourly rate limit reached: {len(recent_sends)}/{max_per_hour}")
			return False
		
		# Update last sent time
		self.last_sent[rate_key] = now
		return True
	
	def _add_to_queue(self, notification_data: Dict):
		"""Add notification to simple queue with size limit"""
		if len(self.notification_queue) >= self.max_queue_size:
			# Remove oldest notification
			self.notification_queue.pop(0)
		
		self.notification_queue.append({
			'timestamp': datetime.now(),
			'data': notification_data
		})
	
	async def send_bond_stress_alert(self, signal: BondStressSignal):
		"""Send bond stress alert via Discord with rate limiting"""
		
		if signal.confidence_score < self.min_confidence_threshold:
			self.logger.debug(f"Signal confidence {signal.confidence_score} below threshold")
			return
		
		# Check rate limiting
		signal_id = f"{signal.signal_strength.value}_{signal.confidence_score:.1f}"
		if not self._should_send_notification('bond_stress', signal_id):
			return
		
		# Format message
		message = self._format_bond_stress_message(signal)
		
		# Send to Discord only (keeping it simple)
		if self.discord_webhook and self.user_preferences.get('discord_settings', {}).get('enabled', True):
			success = await self._send_discord_message(message, signal)
			if success:
				self.stats['total_sent'] += 1
				self.logger.info(f"Discord bond stress alert sent: {signal.signal_strength.value}")
			else:
				self.stats['failed_sends'] += 1
	
	async def send_chip_trading_alerts(self, signals: List[ChipTradingSignal]):
		"""Send AI chip trading alerts via Discord"""
		
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
		max_signals = self.user_preferences.get('discord_settings', {}).get('max_signals_per_batch', 3)
		top_signals = priority_signals[:max_signals]
		
		sent_count = 0
		for signal in top_signals:
			signal_id = f"{signal.symbol}_{signal.signal_type}"
			if not self._should_send_notification('chip_signals', signal_id):
				continue
			
			message = self._format_chip_signal_message(signal)
			
			if self.discord_webhook:
				success = await self._send_discord_message(message, signal, is_chip_signal=True)
				if success:
					sent_count += 1
					self.stats['total_sent'] += 1
		
		if sent_count > 0:
			self.logger.info(f"Discord chip trading alerts sent: {sent_count} signals")
	
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
		"""Send enhanced message to Discord webhook with rich embeds"""
		
		try:
			if not self.discord_webhook:
				return False
			
			discord_settings = self.user_preferences.get('discord_settings', {})
			use_rich_embeds = discord_settings.get('rich_embeds', True)
			
			if use_rich_embeds:
				# Create rich embed
				embed = self._create_discord_embed(message, signal, is_chip_signal)
				payload = {
					"username": "AI Trading Bot",
					"avatar_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png",
					"embeds": [embed]
				}
				
				# Add mention if configured
				if discord_settings.get('use_mentions') and discord_settings.get('mention_role_id'):
					payload["content"] = f"<@&{discord_settings['mention_role_id']}>"
			else:
				# Simple text message
				payload = {
					"username": "AI Trading Bot",
					"content": message
				}
			
			async with aiohttp.ClientSession() as session:
				async with session.post(self.discord_webhook, json=payload) as response:
					if response.status in [200, 204]:
						self.logger.debug("Discord message sent successfully")
						return True
					else:
						self.logger.error(f"Discord webhook failed: {response.status}")
						return False
		
		except Exception as e:
			self.logger.error(f"Error sending Discord message: {e}")
			return False
	
	def _create_discord_embed(self, message: str, signal, is_chip_signal: bool = False):
		"""Create rich Discord embed for trading signals"""
		
		# Determine color and emoji based on signal
		if is_chip_signal:
			if signal.signal_type == "BUY":
				color = 0x00ff00  # Green
				emoji = "🟢"
			elif signal.signal_type == "SELL":
				color = 0xff0000  # Red
				emoji = "🔴"
			else:
				color = 0xffaa00  # Orange
				emoji = "🟡"
			
			title = f"{emoji} AI Chip Signal: {signal.symbol}"
			
			# Create fields for chip signal
			fields = [
				{"name": "📈 Action", "value": signal.signal_type, "inline": True},
				{"name": "🎯 Confidence", "value": f"{signal.confidence_score:.1f}/10", "inline": True},
				{"name": "💰 Entry Price", "value": f"${signal.entry_price:.2f}", "inline": True},
				{"name": "📊 Position Size", "value": f"{signal.suggested_position_size:.1%}", "inline": True},
				{"name": "🔗 Bond Correlation", "value": f"{signal.bond_correlation:.3f}", "inline": True},
				{"name": "📅 Target Horizon", "value": f"{signal.target_horizon_days} days", "inline": True}
			]
			
			if hasattr(signal, 'reasoning') and signal.reasoning:
				fields.append({
					"name": "📝 Reasoning", 
					"value": signal.reasoning[:100] + "..." if len(signal.reasoning) > 100 else signal.reasoning, 
					"inline": False
				})
		else:
			# Bond stress signal
			color_map = {
				SignalStrength.NOW: 0xff0000,    # Red
				SignalStrength.SOON: 0xffaa00,   # Orange
				SignalStrength.WATCH: 0x00ff00,  # Green
				SignalStrength.NEUTRAL: 0x808080 # Gray
			}
			
			emoji_map = {
				SignalStrength.NOW: "🚨",
				SignalStrength.SOON: "⚠️",
				SignalStrength.WATCH: "👀",
				SignalStrength.NEUTRAL: "😐"
			}
			
			color = color_map.get(signal.signal_strength, 0x808080)
			emoji = emoji_map.get(signal.signal_strength, "📊")
			title = f"{emoji} Bond Stress Alert"
			
			fields = [
				{"name": "📈 Signal Strength", "value": signal.signal_strength.value, "inline": True},
				{"name": "🎯 Confidence", "value": f"{signal.confidence_score:.1f}/10", "inline": True},
				{"name": "📊 Yield Curve", "value": f"{signal.yield_curve_spread:.2f} bps", "inline": True},
				{"name": "📉 Bond Volatility", "value": f"{signal.bond_volatility:.4f}", "inline": True},
				{"name": "💡 Action", "value": signal.suggested_action[:50] + "..." if len(signal.suggested_action) > 50 else signal.suggested_action, "inline": False}
			]
		
		embed = {
			"title": title,
			"color": color,
			"timestamp": datetime.now().isoformat(),
			"fields": fields,
			"footer": {
				"text": "AI Chip Trading Signal System",
				"icon_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png"
			}
		}
		
		return embed
	
	async def send_daily_summary(self, 
		bond_signal: BondStressSignal,
		chip_signals: List[ChipTradingSignal],
		portfolio_value: float = None,
		daily_pnl: float = None
	):
		"""Send daily summary report via Discord"""
		
		# Check if daily summary should be sent
		if not self._should_send_notification('daily_summary'):
			return
		
		if not self.user_preferences.get('enabled_notifications', {}).get('daily_summary', True):
			return
		
		summary_embed = self._create_daily_summary_embed(bond_signal, chip_signals, portfolio_value, daily_pnl)
		
		if self.discord_webhook:
			payload = {
				"username": "AI Trading Bot - Daily Summary",
				"avatar_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png",
				"embeds": [summary_embed]
			}
			
			try:
				async with aiohttp.ClientSession() as session:
					async with session.post(self.discord_webhook, json=payload) as response:
						if response.status in [200, 204]:
							self.stats['last_daily_summary'] = datetime.now()
							self.stats['total_sent'] += 1
							self.logger.info("Discord daily summary sent successfully")
						else:
							self.logger.error(f"Discord daily summary failed: {response.status}")
			except Exception as e:
				self.logger.error(f"Error sending Discord daily summary: {e}")
	
	def _create_daily_summary_embed(self, 
		bond_signal: BondStressSignal,
		chip_signals: List[ChipTradingSignal],
		portfolio_value: float = None,
		daily_pnl: float = None
	) -> Dict:
		"""Create Discord embed for daily summary"""
		
		# Count signals by type
		signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "WATCH": 0}
		high_conf_signals = []
		
		for signal in chip_signals:
			signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
			if signal.confidence_score >= 7.0:
				high_conf_signals.append(f"{signal.symbol}: {signal.signal_type}")
		
		# Create fields
		fields = [
			{
				"name": "🏦 Bond Market Status",
				"value": f"**{bond_signal.signal_strength.value}** (Confidence: {bond_signal.confidence_score:.1f}/10)\n"
						f"Yield Curve: {bond_signal.yield_curve_spread:.2f} bps\n"
						f"Action: {bond_signal.suggested_action[:50]}...",
				"inline": False
			},
			{
				"name": "💎 AI Chip Signals Summary",
				"value": f"🟢 **BUY:** {signal_counts['BUY']} | 🔴 **SELL:** {signal_counts['SELL']} | 🟡 **HOLD:** {signal_counts['HOLD']}\n"
						f"🎯 **High Confidence (>7.0):** {len(high_conf_signals)}",
				"inline": False
			}
		]
		
		if high_conf_signals:
			top_signals = ", ".join(high_conf_signals[:3])
			fields.append({
				"name": "⭐ Top Signals",
				"value": top_signals,
				"inline": False
			})
		
		if portfolio_value:
			fields.append({
				"name": "💰 Portfolio Value",
				"value": f"${portfolio_value:,.2f}",
				"inline": True
			})
		
		if daily_pnl is not None:
			pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
			fields.append({
				"name": f"{pnl_emoji} Daily P&L",
				"value": f"${daily_pnl:+,.2f}",
				"inline": True
			})
		
		# Notification stats
		fields.append({
			"name": "📊 Notification Stats",
			"value": f"Sent Today: {self.stats['total_sent']}\nFailed: {self.stats['failed_sends']}",
			"inline": True
		})
		
		embed = {
			"title": "📊 Daily Trading Summary",
			"description": f"**{datetime.now().strftime('%Y-%m-%d')}** - End of Day Report",
			"color": 0x36a64f,  # Green
			"timestamp": datetime.now().isoformat(),
			"fields": fields,
			"footer": {
				"text": "AI Chip Trading Signal System - Daily Summary",
				"icon_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png"
			}
		}
		
		return embed
	
	async def send_error_alert(self, error_message: str, error_type: str = "SYSTEM_ERROR"):
		"""Send error alert via Discord"""
		
		if not self._should_send_notification('error_alerts'):
			return
		
		if not self.user_preferences.get('enabled_notifications', {}).get('error_alerts', True):
			return
		
		embed = {
			"title": "🚨 System Error Alert",
			"description": f"**Error Type:** {error_type}\n\n**Details:** {error_message[:500]}",
			"color": 0xff0000,  # Red
			"timestamp": datetime.now().isoformat(),
			"footer": {
				"text": "AI Chip Trading Signal System - Error Alert",
				"icon_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png"
			}
		}
		
		if self.discord_webhook:
			payload = {
				"username": "AI Trading Bot - ERROR",
				"avatar_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png",
				"embeds": [embed]
			}
			
			try:
				async with aiohttp.ClientSession() as session:
					async with session.post(self.discord_webhook, json=payload) as response:
						if response.status in [200, 204]:
							self.stats['total_sent'] += 1
							self.logger.info(f"Discord error alert sent: {error_type}")
						else:
							self.logger.error(f"Discord error alert failed: {response.status}")
			except Exception as e:
				self.logger.error(f"Error sending Discord error alert: {e}")
	
	def get_notification_stats(self) -> Dict:
		"""Get notification statistics"""
		return {
			"total_sent": self.stats['total_sent'],
			"failed_sends": self.stats['failed_sends'],
			"last_daily_summary": self.stats['last_daily_summary'].isoformat() if self.stats['last_daily_summary'] else None,
			"rate_limited_today": len([ts for ts in self.last_sent.values() if ts.date() == datetime.now().date()]),
			"queue_size": len(self.notification_queue),
			"config_file": str(self.config_file)
		}
	
	async def test_discord_notification(self) -> bool:
		"""Test Discord notification system"""
		
		if not self.discord_webhook:
			self.logger.error("Discord webhook URL not configured")
			return False
		
		test_embed = {
			"title": "🧪 System Test",
			"description": "AI Chip Trading Signal System notification test",
			"color": 0x00ff00,  # Green
			"timestamp": datetime.now().isoformat(),
			"fields": [
				{"name": "Status", "value": "✅ System Operational", "inline": True},
				{"name": "Test Time", "value": datetime.now().strftime("%H:%M:%S"), "inline": True},
				{"name": "Configuration", "value": f"Min Confidence: {self.min_confidence_threshold}\nRate Limit: {self.min_interval_seconds}s", "inline": False}
			],
			"footer": {
				"text": "AI Chip Trading Signal System - Test",
				"icon_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png"
			}
		}
		
		payload = {
			"username": "AI Trading Bot - TEST",
			"avatar_url": "https://cdn-icons-png.flaticon.com/512/2103/2103633.png",
			"embeds": [test_embed]
		}
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(self.discord_webhook, json=payload) as response:
					if response.status in [200, 204]:
						self.logger.info("Discord test notification sent successfully")
						return True
					else:
						self.logger.error(f"Discord test failed: {response.status}")
						return False
		except Exception as e:
			self.logger.error(f"Error testing Discord notification: {e}")
			return False
	
	def test_notifications(self) -> Dict[str, bool]:
		"""Test Discord notification channel"""
		results = {"discord": False}
		
		async def run_test():
			results["discord"] = await self.test_discord_notification()
		
		# Run async test
		asyncio.run(run_test())
		
		return results
