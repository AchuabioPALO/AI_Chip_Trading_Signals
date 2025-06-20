'use client';

import React, { useState, useEffect } from 'react';
import { BacktestResults, formatCurrency, formatPercentage, tradingAPI } from '@/lib/api';

interface Position {
	symbol: string;
	shares: number;
	entry_price: number;
	current_price: number;
	position_value: number;
	pnl: number;
	pnl_percent: number;
	entry_date: string;
	signal_info: {
		type: string;
		confidence: number;
	};
}

interface PortfolioData {
	portfolio_performance: {
		total_value: number;
		total_pnl: number;
		return_percentage: number;
		cash_balance: number;
	};
	current_positions: Position[];
	risk_metrics: any;
	last_updated: string;
}

export const PositionTracker = () => {
	const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
	const [backtestResults, setBacktestResults] = useState<BacktestResults | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [refreshing, setRefreshing] = useState(false);

	// Fetch real portfolio data
	const fetchPortfolioData = async () => {
		setRefreshing(true);
		try {
			const response = await fetch('http://localhost:8000/api/portfolio');
			if (!response.ok) {
				throw new Error(`Portfolio API error: ${response.status}`);
			}
			const data = await response.json();
			setPortfolioData(data);
			setError(null);
		} catch (err) {
			console.error('Failed to fetch portfolio data:', err);
			setError(err instanceof Error ? err.message : 'Failed to fetch portfolio data');
		} finally {
			setRefreshing(false);
		}
	};

	// Initial load and periodic refresh
	useEffect(() => {
		fetchPortfolioData();
		
		// Refresh every 30 seconds
		const interval = setInterval(fetchPortfolioData, 30000);
		
		return () => clearInterval(interval);
	}, []);

	const runBacktest = async () => {
		setLoading(true);
		setError(null);
		try {
			const results = await tradingAPI.runBacktest();
			setBacktestResults(results);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to run backtest');
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="bg-gray-800 rounded-lg p-6">
			<div className="flex justify-between items-center mb-6">
				<h2 className="text-xl font-semibold text-gray-100">
					Portfolio Performance
				</h2>
				<button 
					onClick={fetchPortfolioData}
					disabled={refreshing}
					className="px-3 py-1 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded text-sm font-medium transition-colors flex items-center"
				>
					{refreshing ? (
						<>
							<div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
							Refreshing...
						</>
					) : (
						'Refresh'
					)}
				</button>
			</div>
					{/* Portfolio Summary */}
		<div className="bg-gray-900 rounded-lg p-4 mb-6 border border-gray-700">
			<div className="flex justify-between items-center mb-2">
				<span className="text-gray-400">Total Value</span>
				<span className="text-xl font-bold text-white">
					{portfolioData ? formatCurrency(portfolioData.portfolio_performance.total_value) : '--'}
				</span>
			</div>
			<div className="flex justify-between items-center">
				<span className="text-gray-400">Total P&L</span>
				<span className={`text-xl font-bold ${portfolioData && portfolioData.portfolio_performance.total_pnl < 0 ? 'text-red-400' : 'text-green-400'}`}>
					{portfolioData ? (
						portfolioData.portfolio_performance.total_pnl < 0 ? 
						`-$${Math.abs(portfolioData.portfolio_performance.total_pnl).toLocaleString()}` : 
						`+$${portfolioData.portfolio_performance.total_pnl.toLocaleString()}`
					) : '--'}
				</span>
			</div>
		</div>

			{/* Strategy Performance (Backtest Results) */}
			{backtestResults && (
				<div className="bg-gray-900 rounded-lg p-4 mb-6 border border-gray-700">
					<h3 className="text-lg font-semibold text-gray-200 mb-3">Strategy Performance</h3>
					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<span className="text-gray-400">Total Return:</span>
							<div className={`font-bold ${backtestResults.backtest_results.total_return > 0 ? 'text-green-400' : 'text-red-400'}`}>
								{formatPercentage(backtestResults.backtest_results.total_return)}
							</div>
						</div>
						<div>
							<span className="text-gray-400">Sharpe Ratio:</span>
							<div className="font-bold text-white">
								{backtestResults.backtest_results.sharpe_ratio.toFixed(2)}
							</div>
						</div>
						<div>
							<span className="text-gray-400">Win Rate:</span>
							<div className="font-bold text-blue-400">
								{formatPercentage(backtestResults.backtest_results.win_rate)}
							</div>
						</div>
						<div>
							<span className="text-gray-400">Max Drawdown:</span>
							<div className="font-bold text-red-400">
								{formatPercentage(backtestResults.backtest_results.max_drawdown)}
							</div>
						</div>
					</div>
				</div>
			)}
		{/* Individual Positions */}
		<div className="space-y-4">
			<h3 className="text-lg font-semibold text-gray-200">Current Positions</h3>
			{portfolioData && portfolioData.current_positions.length > 0 ? (
				portfolioData.current_positions.map((position) => (
					<div 
						key={position.symbol}
						className="bg-gray-900 rounded-lg p-4 border border-gray-700"
					>
						<div className="flex justify-between items-start mb-2">
							<div>
								<div className="text-lg font-bold text-white">
									{position.symbol}
								</div>
								<div className="text-sm text-gray-400">
									{position.shares} shares
								</div>
								<div className="text-xs text-gray-500">
									Entered: {position.entry_date}
								</div>
							</div>
							<div className="text-right">
								<div className="text-lg font-bold text-white">
									{formatCurrency(position.current_price)}
								</div>
								<div className={`text-sm font-medium ${position.pnl < 0 ? 'text-red-400' : 'text-green-400'}`}>
									{position.pnl < 0 ? '' : '+'}${position.pnl.toLocaleString()}
								</div>
							</div>
						</div>
						
						<div className="flex justify-between items-center">
							<div className="text-sm text-gray-400">
								P&L: {formatPercentage(position.pnl_percent / 100)}
							</div>
							<div className="flex space-x-2">
								<button className="px-3 py-1 bg-green-600 hover:bg-green-500 rounded text-sm font-medium transition-colors">
									Buy
								</button>
								<button className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm font-medium transition-colors">
									Sell
								</button>
							</div>
						</div>
						
						{/* Price Details */}
						<div className="mt-2 pt-2 border-t border-gray-700">
							<div className="grid grid-cols-2 gap-4 text-xs text-gray-400">
								<div>
									<div>Entry Price:</div>
									<div className="text-white font-medium">
										{formatCurrency(position.entry_price)}
									</div>
								</div>
								<div>
									<div>Current Price:</div>
									<div className="text-white font-medium">
										{formatCurrency(position.current_price)}
									</div>
								</div>
							</div>
						</div>
					</div>
				))
			) : (
				<div className="bg-gray-900 rounded-lg p-4 border border-gray-700 text-center text-gray-400">
					{portfolioData ? 'No positions currently held' : 'Loading positions...'}
				</div>
			)}
		</div>

			{/* Analytics Actions */}
			<div className="mt-6 space-y-2">
				<button 
					onClick={runBacktest}
					disabled={loading}
					className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded-lg font-medium transition-colors flex items-center justify-center"
				>
					{loading ? (
						<>
							<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
							Running Backtest...
						</>
					) : (
						'Run Strategy Backtest'
					)}
				</button>
				
				<button className="w-full px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors">
					Risk Analysis
				</button>
			</div>

			{/* Error Display */}
			{error && (
				<div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
					<div className="text-red-400 text-sm">Error: {error}</div>
				</div>
			)}

			{/* Portfolio Status */}
			{portfolioData && (
				<div className="mt-4 p-3 bg-gray-900/50 border border-gray-700/50 rounded-lg">
					<div className="text-xs text-gray-400 space-y-1">
						<div>Last Updated: {new Date(portfolioData.last_updated).toLocaleString()}</div>
						<div>Cash Balance: {formatCurrency(portfolioData.portfolio_performance.cash_balance)}</div>
						<div>Return: {portfolioData.portfolio_performance.return_percentage.toFixed(2)}%</div>
						{portfolioData.risk_metrics && (
							<div>Risk Level: {portfolioData.risk_metrics.risk_regime}</div>
						)}
					</div>
				</div>
			)}

			{/* Backtest Details */}
			{backtestResults && (
				<div className="mt-4 bg-gray-900 rounded-lg p-4 border border-gray-700">
					<h4 className="text-sm font-semibold text-gray-300 mb-2">Backtest Details</h4>
					<div className="text-xs text-gray-400 space-y-1">
						<div>Period: {backtestResults.period.start} to {backtestResults.period.end}</div>
						<div>Total Trades: {backtestResults.backtest_results.total_trades}</div>
						<div>Avg Hold: {backtestResults.backtest_results.avg_holding_days.toFixed(1)} days</div>
						<div>Best Trade: {formatPercentage(backtestResults.backtest_results.best_trade)}</div>
						<div>Worst Trade: {formatPercentage(backtestResults.backtest_results.worst_trade)}</div>
					</div>
				</div>
			)}
		</div>
	);
};
