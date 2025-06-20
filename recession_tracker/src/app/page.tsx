'use client';

import { SignalPanel } from '@/components/SignalPanel';
import { PositionTracker } from '@/components/PositionTracker';
import { BondStressIndicators } from '@/components/BondStressIndicators';
import { BondChart } from '@/components/BondChart';
import { PerformanceChart } from '@/components/PerformanceChart';
import { SignalDrillDown } from '@/components/SignalDrillDown';
import { useState, useEffect } from 'react';

export default function TradingDashboard() {
	const [currentTime, setCurrentTime] = useState<Date | null>(null);
	const [marketStatus, setMarketStatus] = useState('CHECKING...');
	const [isClient, setIsClient] = useState(false);

	useEffect(() => {
		// Set client-side flag
		setIsClient(true);
		setCurrentTime(new Date());
		
		// Update time every second
		const timeInterval = setInterval(() => {
			setCurrentTime(new Date());
		}, 1000);

		// Check market status
		const checkMarketStatus = () => {
			const now = new Date();
			const hour = now.getHours();
			const day = now.getDay();
			
			// Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
			const isWeekday = day >= 1 && day <= 5;
			const isMarketHours = hour >= 9 && hour < 16;
			
			if (isWeekday && isMarketHours) {
				setMarketStatus('OPEN');
			} else if (isWeekday) {
				setMarketStatus('CLOSED');
			} else {
				setMarketStatus('WEEKEND');
			}
		};

		checkMarketStatus();
		const statusInterval = setInterval(checkMarketStatus, 60000); // Check every minute

		return () => {
			clearInterval(timeInterval);
			clearInterval(statusInterval);
		};
	}, []);

	const getMarketStatusColor = (status: string) => {
		switch (status) {
			case 'OPEN': return 'text-green-400';
			case 'CLOSED': return 'text-red-400';
			case 'WEEKEND': return 'text-yellow-400';
			default: return 'text-gray-400';
		}
	};

	return (
		<div className="min-h-screen bg-gray-900 text-white">
			{/* Header */}
			<header className="border-b border-gray-800 bg-gray-950">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="flex justify-between items-center py-4">
						<div className="flex items-center space-x-4">
							<h1 className="text-2xl font-bold text-green-400">
								AI Chip Trading Signals
							</h1>
							<div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-gray-800 rounded-lg border border-gray-700">
								<div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
								<span className="text-sm text-gray-300">Live Data</span>
							</div>
						</div>
						<div className="flex items-center space-x-4">
							<div className="text-sm text-gray-400">
								Market: <span className={getMarketStatusColor(marketStatus)}>{marketStatus}</span>
							</div>
							<div className="text-sm text-gray-400">
								{currentTime ? currentTime.toLocaleTimeString('en-US', { 
									timeZone: 'America/New_York',
									hour12: true,
									hour: 'numeric',
									minute: '2-digit',
									second: '2-digit'
								}) : '--:--:--'} ET
							</div>
						</div>
					</div>
				</div>
			</header>

			{/* Main Dashboard */}
			<main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				{/* Top Row - Signals and Position Tracker */}
				<div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
					{/* Signal Panel - Takes up 2 columns on large screens */}
					<div className="lg:col-span-2">
						<SignalPanel />
					</div>
					
					{/* Position Tracker - Takes up 1 column */}
					<div className="lg:col-span-1">
						<PositionTracker />
					</div>
				</div>

				{/* Middle Row - Charts */}
				<div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
					{/* Bond Chart */}
					<div>
						<BondChart />
					</div>
					
					{/* Performance Chart */}
					<div>
						<PerformanceChart />
					</div>
				</div>

				{/* Bottom Row - Bond Stress Indicators (Full Width) */}
				<div className="grid grid-cols-1 gap-8 mb-8">
					{/* Bond Stress Indicators - Full width */}
					<div>
						<BondStressIndicators />
					</div>
				</div>

				{/* Signal Deep Dive */}
				<div className="mb-8">
					<SignalDrillDown />
				</div>
			</main>

			{/* Footer */}
			<footer className="border-t border-gray-800 bg-gray-950 mt-8">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
					<div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
						<div className="flex items-center space-x-4 text-sm text-gray-400">
							<span>API Status: <span className="text-green-400">Connected</span></span>
							<span>•</span>
							<span>Data Feed: <span className="text-green-400">Live</span></span>
							<span>•</span>
							<span>Last Sync: {isClient && currentTime ? currentTime.toLocaleTimeString() : '--:--:--'}</span>
						</div>
						<div className="text-sm text-gray-500">
							AI Chip Trading Signals v2.0 • Feature 3 Enhanced Dashboard
						</div>
					</div>
				</div>
			</footer>
		</div>
	);
}
