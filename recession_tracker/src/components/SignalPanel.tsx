'use client';

import React, { useState } from 'react';
import { useChipSignals, ChipSignalData, formatCurrency, formatPercentage, getSignalColor, getSignalEmoji } from '@/lib/api';

const getStatusColor = (status: string) => {
	switch (status) {
		case 'NOW': return 'bg-red-500';
		case 'SOON': return 'bg-yellow-500';
		case 'WATCH': return 'bg-green-500';
		default: return 'bg-gray-500';
	}
};

const getStatusTextColor = (status: string) => {
	switch (status) {
		case 'NOW': return 'text-red-400';
		case 'SOON': return 'text-yellow-400';
		case 'WATCH': return 'text-green-400';
		default: return 'text-gray-400';
	}
};

export const SignalPanel = () => {
	const [selectedTimeframe, setSelectedTimeframe] = useState(20);
	const { data: signals, loading, error } = useChipSignals();

	// Filter signals by selected timeframe
	const filteredSignals = signals.filter(signal => signal.target_horizon_days <= selectedTimeframe);

	if (loading) {
		return (
			<div className="bg-gray-800 rounded-lg p-6">
				<h2 className="text-xl font-semibold mb-6 text-gray-100">
					AI Chip Trading Signals
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
				<h2 className="text-xl font-semibold mb-6 text-gray-100">
					AI Chip Trading Signals
				</h2>
				<div className="text-center text-red-400 py-8">
					Error loading signals: {error}
				</div>
			</div>
		);
	}

	return (
		<div className="bg-gray-800 rounded-lg p-6">
			<h2 className="text-xl font-semibold mb-6 text-gray-100">
				AI Chip Trading Signals
			</h2>
			
			<div className="space-y-4">
				{filteredSignals.map((signal: ChipSignalData, index: number) => (
					<div 
						key={`${signal.symbol}-${index}`}
						className="bg-gray-900 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
					>
						<div className="flex items-center justify-between">
							<div className="flex items-center space-x-4">
								<div className="text-2xl font-bold text-white">
									{signal.symbol}
								</div>
								<div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(signal.signal_strength)} text-white`}>
									{signal.signal_strength} {getSignalEmoji(signal.signal_strength)}
								</div>
								<div className="text-lg font-mono text-gray-300">
									{formatCurrency(signal.entry_price)}
								</div>
							</div>
							
							<div className="flex items-center space-x-6">
								<div className="text-center">
									<div className="text-sm text-gray-400">Confidence</div>
									<div className="text-2xl font-bold text-white">
										{(signal.confidence_score * 100).toFixed(0)}%
									</div>
								</div>
								
								<div className="text-center">
									<div className="text-sm text-gray-400">Correlation</div>
									<div className={`text-lg font-semibold ${signal.bond_correlation > 0 ? 'text-green-400' : 'text-red-400'}`}>
										{formatPercentage(signal.bond_correlation)}
									</div>
								</div>
								
								<div className="text-center">
									<div className="text-sm text-gray-400">Horizon</div>
									<div className="text-lg font-semibold text-blue-400">
										{signal.target_horizon_days}D
									</div>
								</div>
								
								<button 
									className={`px-4 py-2 rounded-lg font-medium transition-colors ${getStatusColor(signal.signal_strength)} hover:opacity-80`}
									title={signal.reasoning}
								>
									View Details
								</button>
							</div>
						</div>
						
						{/* Signal reasoning */}
						<div className="mt-3 pt-3 border-t border-gray-700">
							<div className="text-sm text-gray-400 mb-1">Analysis:</div>
							<div className="text-sm text-gray-300">{signal.reasoning}</div>
						</div>
						
						{/* Position sizing */}
						<div className="mt-2">
							<div className="text-xs text-gray-500">
								Suggested Position: {formatPercentage(signal.suggested_position_size)} of portfolio
							</div>
						</div>
					</div>
				))}
			</div>
			
			{/* Timeframe Toggle */}
			<div className="mt-6 flex items-center justify-center space-x-4">
				<span className="text-gray-400">Max Horizon:</span>
				{[20, 40, 60].map((days) => (
					<button
						key={days}
						onClick={() => setSelectedTimeframe(days)}
						className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
							selectedTimeframe === days
								? 'bg-blue-600 text-white'
								: 'bg-gray-700 hover:bg-gray-600 text-gray-300'
						}`}
					>
						{days}D
					</button>
				))}
			</div>
			
			{/* Summary Stats */}
			<div className="mt-6 grid grid-cols-3 gap-4">
				<div className="bg-gray-900 rounded-lg p-4 text-center">
					<div className="text-2xl font-bold text-white">{filteredSignals.length}</div>
					<div className="text-sm text-gray-400">Active Signals</div>
				</div>
				<div className="bg-gray-900 rounded-lg p-4 text-center">
					<div className="text-2xl font-bold text-red-400">
						{filteredSignals.filter(s => s.signal_strength === 'NOW').length}
					</div>
					<div className="text-sm text-gray-400">NOW Signals</div>
				</div>
				<div className="bg-gray-900 rounded-lg p-4 text-center">
					<div className="text-2xl font-bold text-green-400">
						{filteredSignals.length > 0 
							? formatPercentage(filteredSignals.reduce((sum, s) => sum + s.confidence_score, 0) / filteredSignals.length)
							: '0%'
						}
					</div>
					<div className="text-sm text-gray-400">Avg Confidence</div>
				</div>
			</div>
		</div>
	);
};
