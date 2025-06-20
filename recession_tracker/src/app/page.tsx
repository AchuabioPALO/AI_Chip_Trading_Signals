import { SignalPanel } from '@/components/SignalPanel';
import { PositionTracker } from '@/components/PositionTracker';
import { BondStressIndicators } from '@/components/BondStressIndicators';

export default function TradingDashboard() {
	return (
		<div className="min-h-screen bg-gray-900 text-white">
			{/* Header */}
			<header className="border-b border-gray-800 bg-gray-950">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="flex justify-between items-center py-4">
						<h1 className="text-2xl font-bold text-green-400">
							AI Chip Trading Signals
						</h1>
						<div className="flex items-center space-x-4">
							<div className="text-sm text-gray-400">
								Market Status: <span className="text-green-400">OPEN</span>
							</div>
							<div className="text-sm text-gray-400">
								Last Update: {new Date().toLocaleTimeString()}
							</div>
						</div>
					</div>
				</div>
			</header>

			{/* Main Dashboard */}
			<main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
					{/* Signal Panel - Takes up 2 columns on large screens */}
					<div className="lg:col-span-2">
						<SignalPanel />
					</div>
					
					{/* Position Tracker - Takes up 1 column */}
					<div className="lg:col-span-1">
						<PositionTracker />
					</div>
				</div>

				{/* Bond Stress Indicators - Full width */}
				<div className="mt-8">
					<BondStressIndicators />
				</div>
			</main>
		</div>
	);
}
