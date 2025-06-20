'use client';

import React from 'react';
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
	ArcElement,
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
	ArcElement
);

interface SignalBreakdownChartProps {
	zScoreData: {
		label: string;
		z_score: number;
		threshold: string;
	}[];
}

export const SignalBreakdownChart: React.FC<SignalBreakdownChartProps> = ({ zScoreData }) => {
	// Component weights for signal generation
	const componentWeights = {
		'Yield Curve': 40,
		'Volatility': 35,
		'Credit Spreads': 25
	};

	// Doughnut chart for component weights
	const weightsData = {
		labels: Object.keys(componentWeights),
		datasets: [
			{
				data: Object.values(componentWeights),
				backgroundColor: [
					'rgba(59, 130, 246, 0.8)',  // Blue
					'rgba(245, 158, 11, 0.8)',  // Yellow
					'rgba(34, 197, 94, 0.8)',   // Green
				],
				borderColor: [
					'rgba(59, 130, 246, 1)',
					'rgba(245, 158, 11, 1)',
					'rgba(34, 197, 94, 1)',
				],
				borderWidth: 2,
			},
		],
	};

	const weightsOptions = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'bottom' as const,
				labels: {
					color: '#e5e7eb',
					font: {
						size: 12
					}
				}
			},
			tooltip: {
				backgroundColor: 'rgba(17, 24, 39, 0.95)',
				titleColor: '#f3f4f6',
				bodyColor: '#e5e7eb',
				borderColor: 'rgba(75, 85, 99, 0.8)',
				borderWidth: 1,
				callbacks: {
					label: function(context: any) {
						return `${context.label}: ${context.parsed}%`;
					}
				}
			}
		}
	};

	// Historical z-score trend (mock data)
	const historicalZScores = {
		labels: ['30d ago', '25d ago', '20d ago', '15d ago', '10d ago', '5d ago', 'Today'],
		datasets: [
			{
				label: 'Yield Curve Z-Score',
				data: [-0.8, -0.5, -0.1, 0.2, -0.3, -0.2, zScoreData[0]?.z_score || -0.28],
				borderColor: 'rgba(59, 130, 246, 1)',
				backgroundColor: 'rgba(59, 130, 246, 0.1)',
				borderWidth: 2,
				tension: 0.4,
			},
			{
				label: 'Volatility Z-Score',
				data: [-0.9, -0.7, -0.4, -0.6, -0.8, -0.7, zScoreData[1]?.z_score || -0.65],
				borderColor: 'rgba(245, 158, 11, 1)',
				backgroundColor: 'rgba(245, 158, 11, 0.1)',
				borderWidth: 2,
				tension: 0.4,
			},
			{
				label: 'Credit Z-Score',
				data: [-1.0, -0.8, -0.6, -0.9, -0.7, -0.8, zScoreData[2]?.z_score || -0.76],
				borderColor: 'rgba(34, 197, 94, 1)',
				backgroundColor: 'rgba(34, 197, 94, 0.1)',
				borderWidth: 2,
				tension: 0.4,
			}
		],
	};

	const trendOptions = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'top' as const,
				labels: {
					color: '#e5e7eb',
					font: {
						size: 11
					}
				}
			},
			tooltip: {
				backgroundColor: 'rgba(17, 24, 39, 0.95)',
				titleColor: '#f3f4f6',
				bodyColor: '#e5e7eb',
				borderColor: 'rgba(75, 85, 99, 0.8)',
				borderWidth: 1,
			}
		},
		scales: {
			y: {
				beginAtZero: false,
				grid: {
					color: 'rgba(75, 85, 99, 0.3)',
				},
				ticks: {
					color: '#9ca3af',
					font: {
						size: 10
					}
				},
				title: {
					display: true,
					text: 'Z-Score (σ)',
					color: '#e5e7eb'
				}
			},
			x: {
				grid: {
					color: 'rgba(75, 85, 99, 0.3)',
				},
				ticks: {
					color: '#9ca3af',
					font: {
						size: 10
					}
				}
			},
		},
	};

	return (
		<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
			{/* Component Weights */}
			<div className="bg-gray-900 rounded-lg p-4">
				<h4 className="text-lg font-semibold text-blue-400 mb-3">Signal Component Weights</h4>
				<div className="h-64">
					<Doughnut data={weightsData} options={weightsOptions} />
				</div>
			</div>

			{/* Historical Z-Score Trends */}
			<div className="bg-gray-900 rounded-lg p-4">
				<h4 className="text-lg font-semibold text-purple-400 mb-3">Z-Score Trend (30 Days)</h4>
				<div className="h-64">
					<Line data={historicalZScores} options={trendOptions} />
				</div>
			</div>
		</div>
	);
};
