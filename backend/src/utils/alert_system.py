#!/usr/bin/env python3
"""
Discord Alert System for Bond Stress Monitoring
Implements Feature 01 alert system requirements
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Optional
import os
from dataclasses import asdict

class DiscordAlertSystem:
	"""Discord webhook alert system for bond stress signals"""
	
	def __init__(self, webhook_url: Optional[str] = None):
		self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
		self.logger = logging.getLogger(__name__)
		
	async def send_bond_stress_alert(self, signal):
		"""Send bond stress alert to Discord"""
		if not self.webhook_url:
			self.logger.warning("No Discord webhook URL configured")
			return False
		
		try:
			# Format alert message
			embed = self._create_bond_stress_embed(signal)
			
			payload = {
				"content": f"🚨 **BOND STRESS ALERT** - {signal.signal_strength.value}",
				"embeds": [embed]
			}
			
			async with aiohttp.ClientSession() as session:
				async with session.post(self.webhook_url, json=payload) as response:
					if response.status == 204:
						self.logger.info("✅ Discord alert sent successfully")
						return True
					else:
						self.logger.error(f"❌ Discord alert failed: {response.status}")
						return False
						
		except Exception as e:
			self.logger.error(f"❌ Discord alert error: {e}")
			return False
	
	def _create_bond_stress_embed(self, signal):
		"""Create Discord embed for bond stress signal"""
		
		# Color based on signal strength
		color_map = {
			"NOW": 0xFF0000,     # Red
			"SOON": 0xFF8C00,    # Orange  
			"WATCH": 0xFFD700,   # Yellow
			"NEUTRAL": 0x808080  # Gray
		}
		
		color = color_map.get(signal.signal_strength.value, 0x808080)
		
		embed = {
			"title": f"Bond Market Stress Alert - {signal.signal_strength.value}",
			"description": signal.suggested_action,
			"color": color,
			"timestamp": signal.timestamp.isoformat(),
			"fields": [
				{
					"name": "📈 Yield Curve Spread",
					"value": f"{signal.yield_curve_spread:.2f} bps",
					"inline": True
				},
				{
					"name": "📊 Z-Score",
					"value": f"{signal.yield_curve_zscore:.2f}",
					"inline": True
				},
				{
					"name": "🎯 Confidence",
					"value": f"{signal.confidence_score:.1f}/10",
					"inline": True
				},
				{
					"name": "📉 Bond Volatility",
					"value": f"{signal.bond_volatility:.4f}",
					"inline": True
				},
				{
					"name": "💰 Credit Spreads",
					"value": f"{signal.credit_spreads:.4f}",
					"inline": True
				},
				{
					"name": "⏰ Timestamp",
					"value": signal.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
					"inline": True
				}
			],
			"footer": {
				"text": "AI Chip Trading Signal System | Bond Stress Monitor"
			}
		}
		
		return embed
	
	async def send_correlation_alert(self, symbol: str, correlation: float, signal_type: str):
		"""Send correlation-based trading signal"""
		if not self.webhook_url:
			return False
		
		try:
			embed = {
				"title": f"🔗 Correlation Signal - {symbol}",
				"description": f"**Action:** {signal_type}",
				"color": 0x00FF00 if signal_type == "BUY" else 0xFF0000,
				"fields": [
					{
						"name": "📈 Stock Symbol",
						"value": symbol,
						"inline": True
					},
					{
						"name": "🔗 Bond Correlation",
						"value": f"{correlation:.3f}",
						"inline": True
					},
					{
						"name": "📊 Signal Type",
						"value": signal_type,
						"inline": True
					}
				],
				"timestamp": datetime.now().isoformat()
			}
			
			payload = {
				"content": f"📊 **TRADING SIGNAL** - {symbol}",
				"embeds": [embed]
			}
			
			async with aiohttp.ClientSession() as session:
				async with session.post(self.webhook_url, json=payload) as response:
					return response.status == 204
					
		except Exception as e:
			self.logger.error(f"❌ Correlation alert error: {e}")
			return False
	
	def send_sync_alert(self, signal):
		"""Synchronous wrapper for async alert"""
		try:
			loop = asyncio.get_event_loop()
		except RuntimeError:
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
		
		return loop.run_until_complete(self.send_bond_stress_alert(signal))

# Simple email alert backup system
class EmailAlertSystem:
	"""Simple email alerts for critical signals"""
	
	def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
		self.smtp_server = smtp_server
		self.smtp_port = smtp_port
		self.email = os.getenv('ALERT_EMAIL')
		self.password = os.getenv('ALERT_EMAIL_PASSWORD') 
		self.to_email = os.getenv('ALERT_TO_EMAIL')
		self.logger = logging.getLogger(__name__)
	
	def send_critical_alert(self, signal):
		"""Send email for critical bond stress signals"""
		if not all([self.email, self.password, self.to_email]):
			self.logger.warning("Email configuration incomplete")
			return False
		
		if signal.confidence_score < 8.0:
			return False  # Only send for high confidence signals
		
		try:
			import smtplib
			from email.mime.text import MIMEText
			from email.mime.multipart import MIMEMultipart
			
			msg = MIMEMultipart()
			msg['From'] = self.email
			msg['To'] = self.to_email
			msg['Subject'] = f"CRITICAL: Bond Stress Alert - {signal.signal_strength.value}"
			
			body = f"""
CRITICAL BOND STRESS ALERT

Signal Strength: {signal.signal_strength.value}
Confidence Score: {signal.confidence_score:.1f}/10
Action: {signal.suggested_action}

Details:
- Yield Curve Spread: {signal.yield_curve_spread:.2f} bps
- Z-Score: {signal.yield_curve_zscore:.2f}
- Bond Volatility: {signal.bond_volatility:.4f}
- Credit Spreads: {signal.credit_spreads:.4f}

Timestamp: {signal.timestamp}

AI Chip Trading Signal System
			"""
			
			msg.attach(MIMEText(body, 'plain'))
			
			server = smtplib.SMTP(self.smtp_server, self.smtp_port)
			server.starttls()
			server.login(self.email, self.password)
			text = msg.as_string()
			server.sendmail(self.email, self.to_email, text)
			server.quit()
			
			self.logger.info("✅ Critical email alert sent")
			return True
			
		except Exception as e:
			self.logger.error(f"❌ Email alert failed: {e}")
			return False
