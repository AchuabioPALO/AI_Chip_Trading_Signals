#!/usr/bin/env python3
"""
Quick Discord Webhook Test for AI Chip Trading Signal System
Tests if Discord notifications are working properly
"""

import os
import requests
import json
from datetime import datetime

def test_discord_webhook():
	"""Test Discord webhook with a sample trading signal"""
	
	# Load environment variables
	webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
	
	if not webhook_url:
		print("❌ DISCORD_WEBHOOK_URL not found in environment variables")
		return False
	
	# Create a sample trading signal notification
	sample_signal = {
		"embeds": [{
			"title": "🚀 AI Chip Trading Signal Test",
			"description": "Your AI Chip Trading Signal system is now connected to Discord!",
			"color": 0x00ff00,  # Green color
			"fields": [
				{
					"name": "📊 Signal Type",
					"value": "System Test",
					"inline": True
				},
				{
					"name": "💎 Symbol", 
					"value": "NVDA",
					"inline": True
				},
				{
					"name": "🎯 Signal Strength",
					"value": "STRONG",
					"inline": True
				},
				{
					"name": "💰 Current Price",
					"value": "$145.48",
					"inline": True
				},
				{
					"name": "📈 Confidence",
					"value": "8.5/10",
					"inline": True
				},
				{
					"name": "⏰ Timestamp",
					"value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"inline": True
				}
			],
			"footer": {
				"text": "AI Chip Trading Signal System | Bond Stress Analysis"
			}
		}]
	}
	
	try:
		print("🔔 Sending test notification to Discord...")
		
		response = requests.post(
			webhook_url, 
			json=sample_signal,
			headers={'Content-Type': 'application/json'}
		)
		
		if response.status_code == 204:
			print("✅ SUCCESS! Discord notification sent successfully!")
			print("📱 Check your Discord channel for the test message")
			return True
		else:
			print(f"❌ Failed to send Discord notification. Status code: {response.status_code}")
			print(f"Response: {response.text}")
			return False
			
	except Exception as e:
		print(f"❌ Error sending Discord notification: {str(e)}")
		return False

def test_production_signal():
	"""Test with a realistic trading signal format"""
	
	webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
	
	if not webhook_url:
		return False
	
	# Realistic trading signal
	trading_signal = {
		"embeds": [{
			"title": "⚠️ BOND STRESS ALERT",
			"description": "High-confidence AI chip trading signal detected!",
			"color": 0xff9900,  # Orange color for alerts
			"fields": [
				{
					"name": "📊 Bond Stress Level",
					"value": "ELEVATED (Z-Score: 2.1)",
					"inline": False
				},
				{
					"name": "💎 Recommended Trades",
					"value": "• NVDA: REDUCE 15%\n• AMD: WATCH\n• TSM: HOLD",
					"inline": False
				},
				{
					"name": "⏱️ Signal Horizon",
					"value": "20-60 days",
					"inline": True
				},
				{
					"name": "🎯 Confidence Score",
					"value": "7.8/10",
					"inline": True
				},
				{
					"name": "📈 Expected Return",
					"value": "+8.5% alpha",
					"inline": True
				}
			],
			"footer": {
				"text": "AI Chip Trading Signal System | Real-time bond correlation analysis"
			}
		}]
	}
	
	try:
		response = requests.post(webhook_url, json=trading_signal)
		if response.status_code == 204:
			print("✅ Production-style signal sent successfully!")
			return True
		else:
			print(f"❌ Production signal failed: {response.status_code}")
			return False
	except Exception as e:
		print(f"❌ Error: {str(e)}")
		return False

if __name__ == "__main__":
	print("🚀 Testing AI Chip Trading Signal Discord Integration")
	print("=" * 60)
	
	# Load environment from .env file
	try:
		from dotenv import load_dotenv
		load_dotenv()
		print("✅ Environment variables loaded")
	except ImportError:
		print("⚠️  python-dotenv not found, using system environment")
	
	# Test basic notification
	print("\n1️⃣ Testing basic Discord webhook...")
	success1 = test_discord_webhook()
	
	# Test production-style signal
	print("\n2️⃣ Testing production trading signal...")
	success2 = test_production_signal()
	
	print("\n" + "=" * 60)
	if success1 and success2:
		print("🎉 ALL TESTS PASSED! Your Discord integration is ready for trading!")
		print("💡 Your system will now send real-time trading alerts to Discord")
	else:
		print("❌ Some tests failed. Check your webhook URL and network connection.")
	
	print("\n🔗 Next: Your trading system will automatically send alerts when:")
	print("   • Bond stress levels exceed thresholds")
	print("   • High-confidence AI chip signals are generated")
	print("   • Significant market events are detected")
