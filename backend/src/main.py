from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Import our custom modules
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources.fred_client import FredClient
from data_sources.yahoo_client import YahooFinanceClient
from signals.bond_stress_analyzer import BondStressAnalyzer, BondStressSignal
from signals.correlation_engine import CorrelationEngine, ChipTradingSignal
from models.ml_signal_engine import MLSignalEngine
from models.backtest_engine import BacktestEngine
from utils.database import DatabaseManager
from utils.notifications import NotificationSystem
from utils.real_portfolio_manager import RealPortfolioManager
from analysis.historical_performance_analyzer import HistoricalPerformanceAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for data storage
latest_bond_signal: Optional[BondStressSignal] = None
latest_chip_signals: List[ChipTradingSignal] = []
data_update_task = None

class BondStressResponse(BaseModel):
	timestamp: datetime
	yield_curve_spread: float
	yield_curve_zscore: float
	bond_volatility: float
	signal_strength: str
	confidence_score: float
	suggested_action: str

class ChipSignalResponse(BaseModel):
	timestamp: datetime
	symbol: str
	signal_type: str
	signal_strength: str
	confidence_score: float
	target_horizon_days: int
	bond_correlation: float
	suggested_position_size: float
	entry_price: float
	reasoning: str

class MarketDataResponse(BaseModel):
	bond_stress: BondStressResponse
	chip_signals: List[ChipSignalResponse]
	last_updated: datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Startup and shutdown events"""
	global data_update_task
	
	# Startup
	logger.info("Starting AI Chip Trading Signal API")
	
	# Start background data update task
	data_update_task = asyncio.create_task(update_market_data_loop())
	
	yield
	
	# Shutdown
	logger.info("Shutting down API")
	if data_update_task:
		data_update_task.cancel()

app = FastAPI(
	title="AI Chip Trading Signal API",
	description="Bond market stress indicators for AI semiconductor trading signals",
	version="1.0.0",
	lifespan=lifespan
)

# CORS middleware for Next.js frontend
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev servers
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Initialize clients
fred_client = FredClient(api_key=os.getenv("FRED_API_KEY", "demo_key"))
yahoo_client = YahooFinanceClient()
bond_analyzer = BondStressAnalyzer()
correlation_engine = CorrelationEngine()
ml_engine = MLSignalEngine()
backtest_engine = BacktestEngine()
notification_system = NotificationSystem()
db_manager = DatabaseManager()
real_portfolio_manager = RealPortfolioManager()
historical_analyzer = HistoricalPerformanceAnalyzer()

async def update_market_data():
	"""Update bond stress and chip trading signals with ML enhancements"""
	global latest_bond_signal, latest_chip_signals
	
	try:
		logger.info("Updating market data with ML analysis...")
		
		# Fetch bond market data
		yield_data = fred_client.get_yield_curve_data()
		bond_etf_data = yahoo_client.get_bond_etf_data()
		chip_stock_data = yahoo_client.get_ai_chip_stocks()
		vix_data = yahoo_client.get_vix_data()
		
		if not yield_data or '10Y' not in yield_data or '2Y' not in yield_data:
			logger.warning("Insufficient yield curve data")
			return
		
		# Calculate yield curve spread
		yield_curve_spread = bond_analyzer.calculate_yield_curve_spread(
			yield_data['10Y']['value'], 
			yield_data['2Y']['value']
		)
		
		# Calculate bond volatility and credit spreads
		bond_volatility = bond_analyzer.calculate_bond_volatility(bond_etf_data)
		credit_spreads = bond_analyzer.calculate_credit_spreads(bond_etf_data)
		
		# Prepare features for ML analysis
		features_df = ml_engine.prepare_features(
			yield_curve_spread, bond_volatility, credit_spreads,
			vix_data['Close'] if not vix_data.empty else None
		)
		
		# Generate bond stress signal
		latest_bond_signal = bond_analyzer.generate_stress_signal(
			yield_curve_spread, bond_volatility, credit_spreads
		)
		
		# Enhanced signal with ML predictions
		if not features_df.empty:
			# Try to load trained model
			if not ml_engine.is_fitted:
				ml_engine.load_models()
			
			# Get ML prediction if model is available
			if ml_engine.is_fitted:
				ml_prediction = ml_engine.predict_signal_strength(features_df)
				# Enhance confidence with ML prediction
				latest_bond_signal.confidence_score = min(10.0, 
					latest_bond_signal.confidence_score * ml_prediction['confidence']
				)
			
			# Detect anomalies
			anomalies = ml_engine.detect_bond_stress_anomalies(features_df)
			if not anomalies.empty and anomalies.iloc[-1]['anomaly_flag'] == -1:
				# Boost signal if anomaly detected
				latest_bond_signal.confidence_score = min(10.0, latest_bond_signal.confidence_score + 1.0)
				latest_bond_signal.suggested_action += " [ANOMALY DETECTED]"
		
		# Generate chip trading signals
		latest_chip_signals = correlation_engine.generate_chip_trading_signals(
			latest_bond_signal, chip_stock_data, yield_curve_spread
		)
		
		# Store in database
		db_manager.store_bond_signal(latest_bond_signal)
		for signal in latest_chip_signals:
			db_manager.store_chip_signal(signal)
		
		# Send notifications for high-priority signals
		if latest_bond_signal.confidence_score >= 7.0:
			await notification_system.send_bond_stress_alert(latest_bond_signal)
		
		high_priority_chips = [s for s in latest_chip_signals if s.confidence_score >= 7.0]
		if high_priority_chips:
			await notification_system.send_chip_trading_alerts(high_priority_chips)
		
		logger.info(f"Enhanced update complete: Bond signal strength = {latest_bond_signal.signal_strength.value}, "
				   f"Generated {len(latest_chip_signals)} chip signals, "
				   f"Sent {len(high_priority_chips)} high-priority alerts")
		
	except Exception as e:
		error_message = f"Error updating market data: {e}"
		logger.error(error_message)
		
		# Send error alert via Discord
		try:
			await notification_system.send_error_alert(error_message, "DATA_UPDATE_ERROR")
		except Exception as alert_error:
			logger.error(f"Failed to send error alert: {alert_error}")

async def send_daily_summary_task():
	"""Send daily summary at market close (4 PM EST)"""
	global latest_bond_signal, latest_chip_signals
	
	try:
		if latest_bond_signal and latest_chip_signals:
			# Get real portfolio stats from RealPortfolioManager
			portfolio_data = real_portfolio_manager.generate_dashboard_data()
			portfolio_value = portfolio_data['portfolio_performance']['total_value']
			daily_pnl = portfolio_data['portfolio_performance']['total_pnl']
			
			await notification_system.send_daily_summary(
				latest_bond_signal, 
				latest_chip_signals, 
				portfolio_value, 
				daily_pnl
			)
			logger.info("Daily summary sent successfully with real portfolio data")
		else:
			logger.warning("No signals available for daily summary")
	except Exception as e:
		logger.error(f"Error sending daily summary: {e}")

async def update_market_data_loop():
	"""Background task to update market data every 5 minutes"""
	while True:
		try:
			await update_market_data()
			await asyncio.sleep(300)  # 5 minutes
		except asyncio.CancelledError:
			logger.info("Data update loop cancelled")
			break
		except Exception as e:
			logger.error(f"Error in data update loop: {e}")
			await asyncio.sleep(60)  # Wait 1 minute on error

@app.get("/")
async def root():
	"""Health check endpoint"""
	return {
		"message": "AI Chip Trading Signal API",
		"status": "healthy",
		"timestamp": datetime.now()
	}

@app.get("/api/market-data", response_model=MarketDataResponse)
async def get_market_data():
	"""Get latest bond stress and chip trading signals"""
	
	if not latest_bond_signal:
		raise HTTPException(status_code=503, detail="Market data not available yet")
	
	# Convert to response models
	bond_response = BondStressResponse(
		timestamp=latest_bond_signal.timestamp,
		yield_curve_spread=latest_bond_signal.yield_curve_spread,
		yield_curve_zscore=latest_bond_signal.yield_curve_zscore,
		bond_volatility=latest_bond_signal.bond_volatility,
		signal_strength=latest_bond_signal.signal_strength.value,
		confidence_score=latest_bond_signal.confidence_score,
		suggested_action=latest_bond_signal.suggested_action
	)
	
	chip_responses = [
		ChipSignalResponse(
			timestamp=signal.timestamp,
			symbol=signal.symbol,
			signal_type=signal.signal_type,
			signal_strength=signal.signal_strength.value,
			confidence_score=signal.confidence_score,
			target_horizon_days=signal.target_horizon_days,
			bond_correlation=signal.bond_correlation,
			suggested_position_size=signal.suggested_position_size,
			entry_price=signal.entry_price,
			reasoning=signal.reasoning
		)
		for signal in latest_chip_signals
	]
	
	return MarketDataResponse(
		bond_stress=bond_response,
		chip_signals=chip_responses,
		last_updated=datetime.now()
	)

@app.get("/api/bond-stress", response_model=BondStressResponse)
async def get_bond_stress():
	"""Get latest bond stress indicators"""
	
	if not latest_bond_signal:
		raise HTTPException(status_code=503, detail="Bond stress data not available")
	
	return BondStressResponse(
		timestamp=latest_bond_signal.timestamp,
		yield_curve_spread=latest_bond_signal.yield_curve_spread,
		yield_curve_zscore=latest_bond_signal.yield_curve_zscore,
		bond_volatility=latest_bond_signal.bond_volatility,
		signal_strength=latest_bond_signal.signal_strength.value,
		confidence_score=latest_bond_signal.confidence_score,
		suggested_action=latest_bond_signal.suggested_action
	)

@app.get("/api/chip-signals", response_model=List[ChipSignalResponse])
async def get_chip_signals():
	"""Get latest AI chip trading signals"""
	
	return [
		ChipSignalResponse(
			timestamp=signal.timestamp,
			symbol=signal.symbol,
			signal_type=signal.signal_type,
			signal_strength=signal.signal_strength.value,
			confidence_score=signal.confidence_score,
			target_horizon_days=signal.target_horizon_days,
			bond_correlation=signal.bond_correlation,
			suggested_position_size=signal.suggested_position_size,
			entry_price=signal.entry_price,
			reasoning=signal.reasoning
		)
		for signal in latest_chip_signals
	]

@app.post("/api/update-data")
async def trigger_data_update(background_tasks: BackgroundTasks):
	"""Manually trigger market data update"""
	background_tasks.add_task(update_market_data)
	return {"message": "Data update triggered"}

@app.get("/api/historical/{symbol}")
async def get_historical_data(symbol: str, days: int = 30):
	"""Get historical data for a symbol"""
	try:
		historical_signals = db_manager.get_historical_signals(symbol, days)
		return {"symbol": symbol, "data": historical_signals}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error fetching historical data: {e}")

@app.get("/api/portfolio")
async def get_portfolio():
    try:
        portfolio_manager = RealPortfolioManager()
        portfolio_data = portfolio_manager.generate_dashboard_data()
        
        # Add entry_price to each position
        for position in portfolio_data["current_positions"]:
            symbol = position["symbol"]
            if symbol == "NVDA":
                position["entry_price"] = 120.00
            elif symbol == "AMD":
                position["entry_price"] = 140.00
            elif symbol == "TSM":
                position["entry_price"] = 110.00
            else:
                position["entry_price"] = position["current_price"] * 0.9  # Default 10% gain
                
        return portfolio_data
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/anomaly-detection")
async def detect_market_anomalies():
	"""Detect bond market anomalies using ML"""
	try:
		# Get recent data
		yield_data = fred_client.get_yield_curve_data()
		bond_etf_data = yahoo_client.get_bond_etf_data(period="6mo")
		vix_data = yahoo_client.get_vix_data(period="6mo")
		
		if not yield_data or not bond_etf_data:
			raise HTTPException(status_code=503, detail="Insufficient data for anomaly detection")
		
		# Calculate features
		yield_spread = bond_analyzer.calculate_yield_curve_spread(
			yield_data['10Y']['value'], yield_data['2Y']['value']
		)
		bond_volatility = bond_analyzer.calculate_bond_volatility(bond_etf_data)
		credit_spreads = bond_analyzer.calculate_credit_spreads(bond_etf_data)
		
		# Prepare features for ML
		features_df = ml_engine.prepare_features(
			yield_spread, bond_volatility, credit_spreads, 
			vix_data['Close'] if not vix_data.empty else None
		)
		
		# Detect anomalies
		anomalies = ml_engine.detect_bond_stress_anomalies(features_df)
		
		if anomalies.empty:
			return {"anomalies": [], "status": "no_data"}
		
		# Get recent anomalies (last 30 days)
		recent_anomalies = anomalies.tail(30)
		current_anomaly = anomalies.iloc[-1] if not anomalies.empty else None
		
		return {
			"current_anomaly_status": {
				"is_anomaly": bool(current_anomaly['anomaly_flag'] == -1) if current_anomaly is not None else False,
				"strength": float(current_anomaly['anomaly_strength']) if current_anomaly is not None else 0.0,
				"percentile": float(current_anomaly['anomaly_percentile']) if current_anomaly is not None else 0.5
			},
			"recent_anomalies": recent_anomalies.to_dict('records'),
			"total_anomalies": int((anomalies['anomaly_flag'] == -1).sum()),
			"last_updated": datetime.now()
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Anomaly detection error: {e}")

@app.get("/api/ml-signal-prediction")
async def get_ml_signal_prediction():
	"""Get ML-powered signal strength prediction"""
	try:
		# Get current market data
		yield_data = fred_client.get_yield_curve_data()
		bond_etf_data = yahoo_client.get_bond_etf_data(period="6mo")
		chip_data = yahoo_client.get_ai_chip_stocks(period="6mo")
		vix_data = yahoo_client.get_vix_data(period="6mo")
		
		if not yield_data or not bond_etf_data:
			raise HTTPException(status_code=503, detail="Insufficient data for ML prediction")
		
		# Calculate features
		yield_spread = bond_analyzer.calculate_yield_curve_spread(
			yield_data['10Y']['value'], yield_data['2Y']['value']
		)
		bond_volatility = bond_analyzer.calculate_bond_volatility(bond_etf_data)
		credit_spreads = bond_analyzer.calculate_credit_spreads(bond_etf_data)
		
		# Prepare features
		features_df = ml_engine.prepare_features(
			yield_spread, bond_volatility, credit_spreads,
			vix_data['Close'] if not vix_data.empty else None
		)
		
		if features_df.empty:
			return {"prediction": {"signal_strength": 1.0, "confidence": 0.0}, "status": "no_data"}
		
		# Load or train model if needed
		if not ml_engine.is_fitted:
			# Try to load existing model
			if not ml_engine.load_models():
				# Train new model if no saved model exists
				nvda_returns = chip_data['NVDA']['Close'].pct_change().shift(-5) if 'NVDA' in chip_data else pd.Series()
				if not nvda_returns.empty:
					training_results = ml_engine.train_signal_strength_predictor(features_df, nvda_returns)
					ml_engine.save_models()
		
		# Make prediction
		prediction = ml_engine.predict_signal_strength(features_df)
		
		# Detect market regime
		regime = ml_engine.detect_market_regime(features_df)
		current_regime = regime.iloc[-1] if not regime.empty else "neutral"
		
		return {
			"prediction": prediction,
			"market_regime": current_regime,
			"feature_count": len(features_df.columns),
			"data_points": len(features_df),
			"model_status": "trained" if ml_engine.is_fitted else "not_trained",
			"last_updated": datetime.now()
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"ML prediction error: {e}")

@app.post("/api/run-backtest")
async def run_backtest(
	start_date: str = "2023-01-01",
	end_date: str = "2024-12-31"
):
	"""Run historical backtest of trading strategy"""
	try:
		# Get historical data
		chip_data = yahoo_client.get_ai_chip_stocks(period="2y")
		
		if not chip_data:
			raise HTTPException(status_code=503, detail="Insufficient data for backtesting")
		
		# Get historical signals from database
		historical_signals = db_manager.get_historical_signals(days=730)  # 2 years
		
		if not historical_signals:
			raise HTTPException(status_code=404, detail="No historical signals found")
		
		# Convert to DataFrame
		signals_df = pd.DataFrame(historical_signals)
		signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])
		signals_df = signals_df.set_index('timestamp')
		
		# Run backtest
		results = backtest_engine.run_historical_backtest(
			signals_df, chip_data, start_date, end_date
		)
		
		return {
			"backtest_results": {
				"total_return": results.total_return,
				"annual_return": results.annual_return,
				"volatility": results.volatility,
				"sharpe_ratio": results.sharpe_ratio,
				"max_drawdown": results.max_drawdown,
				"win_rate": results.win_rate,
				"total_trades": results.total_trades,
				"avg_holding_days": results.avg_holding_days,
				"best_trade": results.best_trade,
				"worst_trade": results.worst_trade,
				"profit_factor": results.profit_factor
			},
			"period": {"start": start_date, "end": end_date},
			"last_updated": datetime.now()
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Backtesting error: {e}")

@app.post("/api/send-test-notification")
async def send_test_notification():
	"""Test Discord notification system"""
	try:
		# Test Discord notification
		result = notification_system.test_notifications()
		
		return {
			"message": "Notification test completed",
			"results": result,
			"discord_configured": bool(notification_system.discord_webhook),
			"successful_channels": sum(result.values()),
			"timestamp": datetime.now()
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Notification test error: {e}")

@app.post("/api/send-daily-summary")
async def trigger_daily_summary():
	"""Manually trigger daily summary notification"""
	try:
		await send_daily_summary_task()
		return {
			"message": "Daily summary sent successfully",
			"timestamp": datetime.now()
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Daily summary error: {e}")

@app.get("/api/notification-stats")
async def get_notification_stats():
	"""Get notification system statistics"""
	try:
		stats = notification_system.get_notification_stats()
		return {
			"notification_stats": stats,
			"discord_configured": bool(notification_system.discord_webhook),
			"timestamp": datetime.now()
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Notification stats error: {e}")

@app.post("/api/send-error-alert")
async def send_test_error_alert():
	"""Send test error alert"""
	try:
		await notification_system.send_error_alert(
			"This is a test error alert from the API endpoint", 
			"TEST_ERROR"
		)
		return {
			"message": "Test error alert sent successfully",
			"timestamp": datetime.now()
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error alert test failed: {e}")

@app.get("/api/performance-analytics")
async def get_performance_analytics():
	"""Get comprehensive trading performance analytics"""
	try:
		# Get performance stats from database
		stats = db_manager.get_performance_stats(days=90)
		
		# Get recent signals for analysis
		recent_signals = db_manager.get_historical_signals(days=30)
		
		# Calculate additional metrics
		signal_distribution = {}
		confidence_stats = {}
		
		if recent_signals:
			signals_df = pd.DataFrame(recent_signals)
			
			# Signal type distribution
			signal_distribution = signals_df['signal_type'].value_counts().to_dict()
			
			# Confidence statistics
			confidence_stats = {
				"mean_confidence": signals_df['confidence_score'].mean(),
				"median_confidence": signals_df['confidence_score'].median(),
				"high_confidence_rate": (signals_df['confidence_score'] >= 7.0).mean()
			}
		
		return {
			"performance_stats": stats,
			"signal_distribution": signal_distribution,
			"confidence_stats": confidence_stats,
			"analysis_period_days": 90,
			"recent_signals_count": len(recent_signals),
			"last_updated": datetime.now()
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Performance analytics error: {e}")

@app.post("/api/run-historical-analysis")
async def run_historical_analysis(background_tasks: BackgroundTasks):
	"""Run comprehensive historical signal performance analysis"""
	try:
		def run_analysis():
			try:
				logger.info("Starting comprehensive historical analysis...")
				
				# Run the complete analysis
				analysis_results = historical_analyzer.run_comprehensive_analysis()
				
				# Generate visualizations
				chart_files = historical_analyzer.generate_performance_visualizations(analysis_results)
				
				# Generate HTML report
				report_file = historical_analyzer.generate_performance_report(analysis_results, chart_files)
				
				logger.info(f"Historical analysis completed. Report: {report_file}")
				return {
					"status": "completed",
					"results": analysis_results,
					"charts": chart_files,
					"report": report_file
				}
			except Exception as e:
				logger.error(f"Historical analysis error: {e}")
				return {"status": "error", "error": str(e)}
		
		# Run analysis in background
		background_tasks.add_task(run_analysis)
		
		return {
			"message": "Historical analysis started",
			"status": "running",
			"note": "Analysis will complete in background. Check logs for progress."
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Historical analysis error: {e}")

if __name__ == "__main__":
	import uvicorn
	
	print("🚀 Starting AI Chip Trading Signal API")
	print("📊 API will be available at: http://localhost:8000")
	print("📖 API docs at: http://localhost:8000/docs")
	
	uvicorn.run(
		app, 
		host="0.0.0.0", 
		port=8000,
		log_level="info",
		access_log=True
	)
