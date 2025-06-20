'use client';

import React, { useState } from 'react';
import { BacktestResults, formatCurrency, formatPercentage, tradingAPI } from '@/lib/api';

interface Position {
	symbol: string;
	quantity: number;
	avgPrice: number;
	currentPrice: number;
	pnl: number;
	pnlPercent: number;
}

// For demo purposes - in real implementation, this would come from your portfolio management system
const mockPositions: Position[] = [
	{ symbol: 'NVDA', quantity: 100, avgPrice: 890.00, currentPrice: 875.50, pnl: -1450, pnlPercent: -1.63 },
	{ symbol: 'AMD', quantity: 200, avgPrice: 145.00, currentPrice: 142.25, pnl: -550, pnlPercent: -1.90 },
	{ symbol: 'TSM', quantity: 150, avgPrice: 105.00, currentPrice: 108.75, pnl: 562, pnlPercent: 3.57 },
];

export const PositionTracker = () => {
	const [backtestResults, setBacktestResults] = useState<BacktestResults | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const totalPnl = mockPositions.reduce((sum, pos) => sum + pos.pnl, 0);
	const totalValue = mockPositions.reduce((sum, pos) => sum + (pos.currentPrice * pos.quantity), 0);

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
			<h2 className="text-xl font-semibold mb-6 text-gray-100">
				Portfolio Performance
			</h2>
			
			{/* Portfolio Summary */}
			<div className="bg-gray-900 rounded-lg p-4 mb-6 border border-gray-700">
				<div className="flex justify-between items-center mb-2">
					<span className="text-gray-400">Total Value</span>
					<span className="text-xl font-bold text-white">
						{formatCurrency(totalValue)}
					</span>
				</div>
				<div className="flex justify-between items-center">
					<span className="text-gray-400">Total P&L</span>
					<span className={`text-xl font-bold ${totalPnl < 0 ? 'text-red-400' : 'text-green-400'}`}>
						{totalPnl < 0 ? '-' : '+'}${Math.abs(totalPnl).toLocaleString()}
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
				{mockPositions.map((position) => (
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
									{position.quantity} shares @ {formatCurrency(position.avgPrice)}
								</div>
							</div>
							<div className="text-right">
								<div className="text-lg font-bold text-white">
									{formatCurrency(position.currentPrice)}
								</div>
								<div className={`text-sm font-medium ${position.pnl < 0 ? 'text-red-400' : 'text-green-400'}`}>
									{position.pnl < 0 ? '' : '+'}${position.pnl.toLocaleString()}
								</div>
							</div>
						</div>
						
						<div className="flex justify-between items-center">
							<div className="text-sm text-gray-400">
								P&L: {formatPercentage(position.pnlPercent / 100)}
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
					</div>
				))}
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
