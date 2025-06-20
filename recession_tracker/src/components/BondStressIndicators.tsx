'use client';

import React from 'react';
import { useBondStress, BondStressData, formatPercentage, getSignalColor } from '@/lib/api';

interface BondIndicator {
	name: string;
	value: number;
	change?: number;
	status: 'normal' | 'warning' | 'stress';
	unit?: string;
}

const getStatusFromSignalStrength = (signalStrength: string): 'normal' | 'warning' | 'stress' => {
	switch (signalStrength) {
		case 'NOW': return 'stress';
		case 'SOON': return 'warning';
		case 'WATCH': return 'warning';
		default: return 'normal';
	}
};

const getStatusColor = (status: string) => {
	switch (status) {
		case 'stress': return 'text-red-400 bg-red-900/20 border-red-500/30';
		case 'warning': return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
		case 'normal': return 'text-green-400 bg-green-900/20 border-green-500/30';
		default: return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
	}
};

const getStatusIcon = (status: string) => {
	switch (status) {
		case 'stress': return '🔴';
		case 'warning': return '🟡';
		case 'normal': return '🟢';
		default: return '⚪';
	}
};

const getOverallStressColor = (signalStrength: string) => {
	switch (signalStrength) {
		case 'NOW': return 'text-red-400';
		case 'SOON': return 'text-yellow-400';
		case 'WATCH': return 'text-green-400';
		default: return 'text-gray-400';
	}
};

export const BondStressIndicators = () => {
	const { data: bondStress, loading, error } = useBondStress();

	// Create indicators from API data - USE REAL BACKEND Z-SCORES
	const createIndicators = (data: BondStressData | null): BondIndicator[] => {
		if (!data) return [];

		const status = getStatusFromSignalStrength(data.signal_strength);
		
		// Use REAL z-score from backend instead of calculating fake one
		const realZScore = data.yield_curve_zscore || 0.0;
		
		return [
			{
				name: '10Y-2Y Yield Spread',
				value: data.yield_curve_spread,
				status,
				unit: 'bps'
			},
			{
				name: 'Spread Z-Score',
				value: realZScore, // REAL z-score from backend
				status,
				unit: 'σ'
			},
			{
				name: 'Bond Volatility',
				value: data.bond_volatility * 100, // Convert to percentage
				status,
				unit: '%'
			},
			{
				name: 'Confidence Score',
				value: data.confidence_score,
				status,
				unit: '/10'
			}
		];
	};

	const indicators = createIndicators(bondStress);

	if (loading) {
		return (
			<div className="bg-gray-800 rounded-lg p-6">
				<h2 className="text-xl font-semibold text-gray-100 mb-6">
					Bond Market Stress Indicators
				</h2>
				<div className="flex items-center justify-center h-64">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="bg-gray-800 rounded-lg p-6">
				<h2 className="text-xl font-semibold text-gray-100 mb-6">
					Bond Market Stress Indicators
				</h2>
				<div className="text-center text-red-400 py-8">
					Error loading bond stress data: {error}
				</div>
			</div>
		);
	}

	return (
		<div className="bg-gray-800 rounded-lg p-6">
			<div className="flex justify-between items-center mb-6">
				<h2 className="text-xl font-semibold text-gray-100">
					Bond Market Stress Indicators
				</h2>
				<div className="text-sm text-gray-400">
					Last updated: {bondStress ? new Date(bondStress.timestamp).toLocaleString() : 'N/A'}
				</div>
			</div>
			
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
				{indicators.map((indicator) => (
					<div 
						key={indicator.name}
						className={`rounded-lg p-4 border ${getStatusColor(indicator.status)}`}
					>
						<div className="flex items-center justify-between mb-2">
							<div className="text-sm font-medium text-gray-300">
								{indicator.name}
							</div>
							<div className="text-lg">
								{getStatusIcon(indicator.status)}
							</div>
						</div>
						
						<div className="flex items-end justify-between">
							<div>
								<div className="text-2xl font-bold text-white">
									{typeof indicator.value === 'number' ? indicator.value.toFixed(2) : indicator.value}
									{indicator.unit && (
										<span className="text-sm text-gray-400 ml-1">
											{indicator.unit}
										</span>
									)}
								</div>
								{indicator.change !== undefined && (
									<div className={`text-sm font-medium ${indicator.change < 0 ? 'text-red-400' : 'text-green-400'}`}>
										{indicator.change > 0 ? '+' : ''}{indicator.change.toFixed(2)}
										{indicator.unit && ` ${indicator.unit}`}
									</div>
								)}
							</div>
						</div>
					</div>
				))}
			</div>

			{/* Bond Market Summary */}
			<div className="mt-6 bg-gray-900 rounded-lg p-4 border border-gray-700">
				<div className="flex items-center justify-between">
					<div>
						<h3 className="text-lg font-semibold text-white mb-1">
							Overall Bond Stress Level
						</h3>
						<p className="text-sm text-gray-400">
							{bondStress?.suggested_action || 'Composite score based on yield curve, volatility, and credit metrics'}
						</p>
					</div>
					<div className="text-right">
						<div className={`text-3xl font-bold ${bondStress ? getOverallStressColor(bondStress.signal_strength) : 'text-gray-400'}`}>
							{bondStress?.signal_strength || 'N/A'}
						</div>
						<div className="text-sm text-gray-400">
							Score: {bondStress?.confidence_score.toFixed(1) || '0'}/10
						</div>
					</div>
				</div>
			</div>

			{/* Real-time Analysis */}
			<div className="mt-4 bg-gray-900 rounded-lg p-4 border border-gray-700">
				<h3 className="text-sm font-semibold text-gray-300 mb-2">
					Current Analysis
				</h3>
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-400">
					<div>
						<span className="font-medium">Signal Strength:</span> {bondStress?.signal_strength || 'N/A'}
					</div>
					<div>
						<span className="font-medium">Confidence:</span> {bondStress?.confidence_score.toFixed(1) || '0'}/10
					</div>
					<div>
						<span className="font-medium">Yield Curve:</span> {bondStress?.yield_curve_spread.toFixed(2) || '0'} bps
					</div>
					<div>
						<span className="font-medium">Z-Score:</span> {bondStress ? bondStress.yield_curve_zscore.toFixed(2) : '0.00'}σ
					</div>
				</div>
				{bondStress?.suggested_action && (
					<div className="mt-3 pt-3 border-t border-gray-700">
						<span className="font-medium text-gray-300">Recommended Action:</span>
						<p className="text-gray-400 mt-1">{bondStress.suggested_action}</p>
					</div>
				)}
			</div>
		</div>
	);
};
