'use client';

import React, { useState, useEffect } from 'react';
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
	Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useBondStress } from '@/lib/api';

ChartJS.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
	Filler
);

interface HistoricalBondData {
	timestamp: string;
	yield_curve_spread: number;
	yield_curve_zscore: number;
	bond_volatility: number;
	signal_strength: string;
}

export const BondChart = () => {
	const { data: currentBondStress } = useBondStress();
	const [historicalData, setHistoricalData] = useState<HistoricalBondData[]>([]);
	const [timeframe, setTimeframe] = useState(30);
	const [loading, setLoading] = useState(true);
	const [chartType, setChartType] = useState<'spread' | 'zscore' | 'volatility'>('spread');

	useEffect(() => {
		const fetchHistoricalData = async () => {
			setLoading(true);
			try {
				// Fetch REAL historical data from backend API
				const response = await fetch(`http://localhost:8000/api/historical-bond-data?days=${timeframe}`);
				if (response.ok) {
					const realData = await response.json();
					setHistoricalData(realData);
				} else {
					// Fallback: Generate single data point from current real data if API fails
					if (currentBondStress) {
						const singlePoint: HistoricalBondData = {
							timestamp: new Date().toISOString(),
							yield_curve_spread: currentBondStress.yield_curve_spread,
							yield_curve_zscore: currentBondStress.yield_curve_zscore,
							bond_volatility: currentBondStress.bond_volatility,
							signal_strength: currentBondStress.signal_strength
						};
						setHistoricalData([singlePoint]);
					}
				}
			} catch (error) {
				console.error('Error fetching historical bond data:', error);
				// Use current real data as fallback instead of fake data
				if (currentBondStress) {
					const singlePoint: HistoricalBondData = {
						timestamp: new Date().toISOString(),
						yield_curve_spread: currentBondStress.yield_curve_spread,
						yield_curve_zscore: currentBondStress.yield_curve_zscore,
						bond_volatility: currentBondStress.bond_volatility,
						signal_strength: currentBondStress.signal_strength
					};
					setHistoricalData([singlePoint]);
				}
			} finally {
				setLoading(false);
			}
		};

		fetchHistoricalData();
	}, [timeframe, currentBondStress]);

		const getChartData = () => {
		const labels = historicalData.map(d => 
			new Date(d.timestamp).toLocaleDateString('en-US', { 
				month: 'short', 
				day: 'numeric' 
			})
		);

		let dataValues: number[];
		let label: string;
		let borderColor: string;
		let backgroundColor: string;

		switch (chartType) {
			case 'spread':
				dataValues = historicalData.map(d => d.yield_curve_spread);
				label = '10Y-2Y Yield Spread (bps)';
				borderColor = 'rgb(59, 130, 246)';
				backgroundColor = 'rgba(59, 130, 246, 0.1)';
				break;
			case 'zscore':
				dataValues = historicalData.map(d => d.yield_curve_zscore);
				label = 'Yield Curve Z-Score';
				borderColor = 'rgb(239, 68, 68)';
				backgroundColor = 'rgba(239, 68, 68, 0.1)';
				break;
			case 'volatility':
				dataValues = historicalData.map(d => d.bond_volatility * 100);
				label = 'Bond Volatility (%)';
				borderColor = 'rgb(34, 197, 94)';
				backgroundColor = 'rgba(34, 197, 94, 0.1)';
				break;
		}

		return {
			labels,
			datasets: [
				{
					label,
					data: dataValues,
					borderColor,
					backgroundColor,
					borderWidth: 2,
					fill: true,
					tension: 0.1,
					pointBackgroundColor: borderColor,
					pointBorderColor: '#fff',
					pointBorderWidth: 2,
					pointRadius: 3,
					pointHoverRadius: 6,
				}
			]
		};
	};

	const chartOptions = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'top' as const,
				labels: {
					color: '#e5e7eb',
					font: {
						size: 12
					}
				}
			},
			title: {
				display: true,
				text: `Bond Market ${chartType === 'spread' ? 'Yield Spread' : chartType === 'zscore' ? 'Stress Levels' : 'Volatility'} - ${timeframe}D`,
				color: '#f9fafb',
				font: {
					size: 16,
					weight: 'bold' as const
				}
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
						const suffix = chartType === 'spread' ? ' bps' : chartType === 'zscore' ? 'σ' : '%';
						return `${context.dataset.label}: ${value.toFixed(2)}${suffix}`;
					}
				}
			}
		},
		scales: {
			x: {
				grid: {
					color: '#374151',
					drawBorder: false
				},
								ticks: {
					color: '#9ca3af',
					font: {
						size: 11
					}
				}
			},
			y: {
				grid: {
					color: '#374151',
					drawBorder: false
				},
				ticks: {
					color: '#9ca3af',
					font: {
						size: 11
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

	if (loading) {
		return (
			<div className="bg-gray-800 rounded-lg p-6">
				<h2 className="text-xl font-semibold mb-6 text-gray-100">
					Bond Market Charts
				</h2>
				<div className="flex items-center justify-center h-64">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
				</div>
			</div>
		);
	}

	return (
		<div className="bg-gray-800 rounded-lg p-6">
			<div className="flex justify-between items-center mb-6">
				<h2 className="text-xl font-semibold text-gray-100">
					Bond Market Charts
				</h2>
				<div className="text-sm text-gray-400">
					Current: {currentBondStress?.signal_strength || 'N/A'} Signal
				</div>
			</div>

			{/* Chart Type Toggles */}
			<div className="mb-4 flex items-center justify-between flex-wrap gap-4">
				<div className="flex items-center space-x-2">
					<span className="text-gray-400 text-sm">Chart Type:</span>
					{[
						{ key: 'spread', label: 'Yield Spread', icon: '📈' },
						{ key: 'zscore', label: 'Z-Score', icon: '📊' },
						{ key: 'volatility', label: 'Volatility', icon: '⚡' }
					].map((type) => (
						<button
							key={type.key}
							onClick={() => setChartType(type.key as any)}
							className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
								chartType === type.key
									? 'bg-blue-600 text-white'
									: 'bg-gray-700 hover:bg-gray-600 text-gray-300'
							}`}
						>
							{type.icon} {type.label}
						</button>
					))}
				</div>

				{/* Timeframe Toggle */}
				<div className="flex items-center space-x-2">
					<span className="text-gray-400 text-sm">Period:</span>
					{[7, 30, 60].map((days) => (
						<button
							key={days}
							onClick={() => setTimeframe(days)}
							className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
								timeframe === days
									? 'bg-green-600 text-white'
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
				<Line data={getChartData()} options={chartOptions} />
			</div>

			{/* Chart Summary */}
			<div className="mt-4 grid grid-cols-3 gap-4">
				<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
					<div className="text-lg font-bold text-blue-400">
						{historicalData.length > 0 ? historicalData[historicalData.length - 1].yield_curve_spread.toFixed(1) : '0'}
					</div>
					<div className="text-xs text-gray-400">Current Spread (bps)</div>
				</div>
				<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
					<div className="text-lg font-bold text-red-400">
						{historicalData.length > 0 ? historicalData[historicalData.length - 1].yield_curve_zscore.toFixed(2) : '0'}σ
					</div>
					<div className="text-xs text-gray-400">Z-Score Level</div>
				</div>
				<div className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
					<div className="text-lg font-bold text-green-400">
						{historicalData.length > 0 ? (historicalData[historicalData.length - 1].bond_volatility * 100).toFixed(1) : '0'}%
					</div>
					<div className="text-xs text-gray-400">Bond Volatility</div>
				</div>
			</div>
		</div>
	);
};
