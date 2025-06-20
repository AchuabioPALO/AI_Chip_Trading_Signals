'use client';

import React, { useState, useEffect } from 'react';
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	BarElement,
	Title,
	Tooltip,
	Legend,
	Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { formatCurrency, formatPercentage } from '@/lib/api';

ChartJS.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	BarElement,
	Title,
	Tooltip,
	Legend,
	Filler
);

interface PerformanceData {
	date: string;
	portfolioValue: number;
	dailyReturn: number;
	cumulativeReturn: number;
	drawdown: number;
}

export const PerformanceChart = () => {
	const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
	const [chartType, setChartType] = useState<'portfolio' | 'returns' | 'drawdown'>('portfolio');
	const [timeframe, setTimeframe] = useState(30);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		const generatePerformanceData = () => {
			const data: PerformanceData[] = [];
			const startValue = 100000; // $100k starting portfolio
			let currentValue = startValue;
			let peak = startValue;
			
			const now = new Date();
			
			for (let i = timeframe; i >= 0; i--) {
				const date = new Date(now);
				date.setDate(date.getDate() - i);
				
				// Generate realistic returns with some correlation to market cycles
				const baseReturn = (Math.random() - 0.48) * 0.02; // Slight positive bias
				const volatility = 0.01 + Math.abs(Math.sin(i * 0.1)) * 0.015;
				const dailyReturn = baseReturn + (Math.random() - 0.5) * volatility;
				
				currentValue = currentValue * (1 + dailyReturn);
				peak = Math.max(peak, currentValue);
				const drawdown = (currentValue - peak) / peak;
				
				const cumulativeReturn = (currentValue - startValue) / startValue;
				
				data.push({
					date: date.toISOString().split('T')[0],
					portfolioValue: currentValue,
					dailyReturn: dailyReturn * 100, // Convert to percentage
					cumulativeReturn: cumulativeReturn * 100,
					drawdown: drawdown * 100
				});
			}
			
			setPerformanceData(data);
			setLoading(false);
		};

		generatePerformanceData();
	}, [timeframe]);

	const getChartData = () => {
		const labels = performanceData.map(d => 
			new Date(d.date).toLocaleDateString('en-US', { 
				month: 'short', 
				day: 'numeric' 
			})
		);

		switch (chartType) {
			case 'portfolio':
				return {
					labels,
					datasets: [
						{
							label: 'Portfolio Value',
							data: performanceData.map(d => d.portfolioValue),
							borderColor: 'rgb(34, 197, 94)',
							backgroundColor: 'rgba(34, 197, 94, 0.1)',
							borderWidth: 2,
							fill: true,
							tension: 0.1,
							pointBackgroundColor: 'rgb(34, 197, 94)',
							pointBorderColor: '#fff',
							pointBorderWidth: 2,
							pointRadius: 2,
							pointHoverRadius: 5,
						}
					]
				};

			case 'returns':
				return {
					labels,
					datasets: [
						{
							label: 'Daily Returns (%)',
							data: performanceData.map(d => d.dailyReturn),
							backgroundColor: performanceData.map(d => 
								d.dailyReturn >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)'
							),
							borderColor: performanceData.map(d => 
								d.dailyReturn >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
							),
							borderWidth: 1,
						}
					]
				};

			case 'drawdown':
				return {
					labels,
					datasets: [
						{
							label: 'Drawdown (%)',
							data: performanceData.map(d => d.drawdown),
							borderColor: 'rgb(239, 68, 68)',
							backgroundColor: 'rgba(239, 68, 68, 0.2)',
							borderWidth: 2,
							fill: true,
							tension: 0.1,
							pointBackgroundColor: 'rgb(239, 68, 68)',
							pointBorderColor: '#fff',
							pointBorderWidth: 2,
							pointRadius: 2,
							pointHoverRadius: 5,
						}
					]
				};

			default:
				return { labels: [], datasets: [] };
		}
	};

	const getChartOptions = () => {
		const baseOptions = {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					position: 'top' as const,
					labels: {
						color: '#e5e7eb',
						font: { size: 12 }
					}
				},
				title: {
					display: true,
					text: `${chartType === 'portfolio' ? 'Portfolio Value' : chartType === 'returns' ? 'Daily Returns' : 'Drawdown'} - ${timeframe}D`,
					color: '#f9fafb',
					font: { size: 16, weight: 'bold' as const }
				},
				tooltip: {
					mode: 'index' as const,
					intersect: false,
					backgroundColor: 'rgba(17, 24, 39, 0.95)',
					titleColor: '#f9fafb',
					bodyColor: '#e5e7eb',
					borderColor: '#374151',
					borderWidth: 1,
					callbacks: {
						label: function(context: any) {
							const value = context.parsed.y;
							if (chartType === 'portfolio') {
								return `Portfolio Value: ${formatCurrency(value)}`;
							} else {
								return `${context.dataset.label}: ${value.toFixed(2)}%`;
							}
						}
					}
				}
			},
			scales: {
				x: {
					grid: { color: '#374151', drawBorder: false },
					ticks: { color: '#9ca3af', font: { size: 11 } }
				},
				y: {
					grid: { color: '#374151', drawBorder: false },
					ticks: { 
						color: '#9ca3af', 
						font: { size: 11 },
						callback: function(value: any) {
							if (chartType === 'portfolio') {
								return formatCurrency(value);
							} else {
								return value.toFixed(1) + '%';
							}
						}
					}
				}
			},
			interaction: {
				mode: 'nearest' as const,
				axis: 'x' as const,
				intersect: false
			}
		};

		return baseOptions;
	};

	const calculateStats = () => {
		if (performanceData.length === 0) return null;

		const returns = performanceData.map(d => d.dailyReturn / 100);
		const finalValue = performanceData[performanceData.length - 1].portfolioValue;
		const startValue = performanceData[0].portfolioValue;
		const totalReturn = (finalValue - startValue) / startValue;
		
		const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
		const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
		const volatility = Math.sqrt(variance) * Math.sqrt(252); // Annualized
		const sharpeRatio = avgReturn * 252 / volatility; // Assuming 0% risk-free rate
		
		const maxDrawdown = Math.min(...performanceData.map(d => d.drawdown));
		const winRate = returns.filter(r => r > 0).length / returns.length;

		return {
			totalReturn,
			annualizedReturn: avgReturn * 252,
			volatility,
			sharpeRatio,
			maxDrawdown,
			winRate,
			currentValue: finalValue
		};
	};

	const stats = calculateStats();

	if (loading) {
		return (
			<div className="bg-gray-800 rounded-lg p-6">
				<h2 className="text-xl font-semibold mb-6 text-gray-100">
					Performance Analytics
				</h2>
				<div className="flex items-center justify-center h-64">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
				</div>
			</div>
		);
	}

	return (
		<div className="bg-gray-800 rounded-lg p-6">
			<div className="flex justify-between items-center mb-6">
				<h2 className="text-xl font-semibold text-gray-100">
					Performance Analytics
				</h2>
				<div className="text-sm text-gray-400">
					{stats ? formatCurrency(stats.currentValue) : 'N/A'}
				</div>
			</div>

			{/* Chart Type and Timeframe Controls */}
			<div className="mb-4 flex items-center justify-between flex-wrap gap-4">
				<div className="flex items-center space-x-2">
					<span className="text-gray-400 text-sm">View:</span>
					{[
						{ key: 'portfolio', label: 'Portfolio', icon: '💰' },
						{ key: 'returns', label: 'Returns', icon: '📊' },
						{ key: 'drawdown', label: 'Drawdown', icon: '📉' }
					].map((type) => (
						<button
							key={type.key}
							onClick={() => setChartType(type.key as any)}
							className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
								chartType === type.key
									? 'bg-green-600 text-white'
									: 'bg-gray-700 hover:bg-gray-600 text-gray-300'
							}`}
						>
							{type.icon} {type.label}
						</button>
					))}
				</div>

				<div className="flex items-center space-x-2">
					<span className="text-gray-400 text-sm">Period:</span>
					{[7, 30, 90].map((days) => (
						<button
							key={days}
							onClick={() => setTimeframe(days)}
							className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
								timeframe === days
									? 'bg-blue-600 text-white'
									: 'bg-gray-700 hover:bg-gray-600 text-gray-300'
							}`}
						>
							{days}D
						</button>
					))}
				</div>
			</div>

			{/* Chart Container */}
			<div className="h-80 bg-gray-900 rounded-lg p-4 border border-gray-700">
				{chartType === 'returns' ? (
					<Bar data={getChartData()} options={getChartOptions()} />
				) : (
					<Line data={getChartData()} options={getChartOptions()} />
				)}
			</div>

			{/* Performance Stats */}
			{stats && (
				<div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
					<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
						<div className={`text-lg font-bold ${stats.totalReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
							{formatPercentage(stats.totalReturn)}
						</div>
						<div className="text-xs text-gray-400">Total Return</div>
					</div>
					<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
						<div className="text-lg font-bold text-blue-400">
							{stats.sharpeRatio.toFixed(2)}
						</div>
						<div className="text-xs text-gray-400">Sharpe Ratio</div>
					</div>
					<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
						<div className="text-lg font-bold text-yellow-400">
							{formatPercentage(stats.winRate)}
						</div>
						<div className="text-xs text-gray-400">Win Rate</div>
					</div>
					<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
						<div className="text-lg font-bold text-red-400">
							{formatPercentage(stats.maxDrawdown / 100)}
						</div>
						<div className="text-xs text-gray-400">Max Drawdown</div>
					</div>
				</div>
			)}
		</div>
	);
};
