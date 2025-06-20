import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import { useBondStress } from '@/lib/api';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface SignalComponent {
    name: string;
    weight: number;
    zscore: number;
    value: number;
    color: string;
}

export default function SignalBreakdownChart() {
    const { data: bondData, loading, error } = useBondStress();

    if (loading) return <div className="animate-pulse bg-gray-800 rounded-lg h-64"></div>;
    if (error) return <div className="text-red-400 p-4">Error loading signal data</div>;

    // Helper function to calculate approximate z-scores for components without backend z-scores
    const calculateApproximateZScore = (value: number, mean: number, std: number) => {
        return (value - mean) / std;
    };

    const components: SignalComponent[] = [
        {
            name: 'Yield Curve',
            weight: 40,
            zscore: bondData?.yield_curve_zscore || 0,
            value: bondData?.yield_curve_spread || 0,
            color: '#3B82F6'
        },
        {
            name: 'Volatility',
            weight: 35,
            // Calculate approximate z-score for volatility (using historical averages)
            zscore: bondData ? calculateApproximateZScore(
                bondData.bond_volatility * 100, // Convert to percentage
                18.5, // Historical mean volatility (%)
                6.2   // Historical std deviation
            ) : 0,
            value: bondData?.bond_volatility || 0,
            color: '#EF4444'
        },
        {
            name: 'Credit Spreads',
            weight: 25,
            // Calculate approximate z-score for credit spreads (using historical averages)
            zscore: bondData ? calculateApproximateZScore(
                bondData.credit_spreads,
                0.002, // Historical mean credit spread
                0.008  // Historical std deviation
            ) : 0,
            value: bondData?.credit_spreads || 0,
            color: '#10B981'
        }
    ];

    // Component weights doughnut chart data
    const weightsData = {
        labels: components.map(c => c.name),
        datasets: [{
            data: components.map(c => c.weight),
            backgroundColor: components.map(c => c.color),
            borderColor: '#1F2937',
            borderWidth: 2,
        }]
    };

    // Z-score trends line chart data
    const zscoreData = {
        labels: components.map(c => c.name),
        datasets: [{
            label: 'Current Z-Score',
            data: components.map(c => c.zscore),
            borderColor: '#F59E0B',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            fill: true,
        }]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#E5E7EB'
                }
            }
        },
        scales: {
            y: {
                grid: {
                    color: '#374151'
                },
                ticks: {
                    color: '#9CA3AF'
                }
            },
            x: {
                grid: {
                    color: '#374151'
                },
                ticks: {
                    color: '#9CA3AF'
                }
            }
        }
    };

    return (
        <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-xl font-bold text-white mb-6">Signal Component Breakdown</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Component Weights */}
                <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-white mb-4">Component Weights</h4>
                    <div className="h-64">
                        <Doughnut data={weightsData} options={chartOptions} />
                    </div>
                </div>

                {/* Z-Score Levels */}
                <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-white mb-4">Current Z-Scores</h4>
                    <div className="h-64">
                        <Line data={zscoreData} options={chartOptions} />
                    </div>
                </div>
            </div>

            {/* Component Details Table */}
            <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm text-left text-gray-300">
                    <thead className="text-xs text-gray-400 uppercase bg-gray-800">
                        <tr>
                            <th className="px-6 py-3">Component</th>
                            <th className="px-6 py-3">Weight</th>
                            <th className="px-6 py-3">Current Value</th>
                            <th className="px-6 py-3">Z-Score</th>
                            <th className="px-6 py-3">Signal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {components.map((comp, index) => (
                            <tr key={index} className="bg-gray-900 border-b border-gray-700">
                                <td className="px-6 py-4 font-medium text-white">{comp.name}</td>
                                <td className="px-6 py-4">{comp.weight}%</td>
                                <td className="px-6 py-4">{comp.value.toFixed(3)}</td>
                                <td className="px-6 py-4 font-mono">
                                    <span className={`${Math.abs(comp.zscore) > 2 ? 'text-red-400' : 
                                        Math.abs(comp.zscore) > 1 ? 'text-yellow-400' : 'text-green-400'}`}>
                                        {comp.zscore.toFixed(2)}σ
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                        Math.abs(comp.zscore) > 2 ? 'bg-red-900 text-red-300' :
                                        Math.abs(comp.zscore) > 1 ? 'bg-yellow-900 text-yellow-300' :
                                        'bg-green-900 text-green-300'
                                    }`}>
                                        {Math.abs(comp.zscore) > 2 ? 'HIGH' : 
                                         Math.abs(comp.zscore) > 1 ? 'MEDIUM' : 'LOW'}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}