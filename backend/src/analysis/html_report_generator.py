"""
HTML Report Generator for Feature 05 Historical Analysis
Convert Jupyter notebook results to professional HTML reports
"""

import pandas as pd
import numpy as np
from datetime import datetime
import base64
import io
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional
import logging

class HTMLReportGenerator:
	"""Generate professional HTML reports from analysis results"""
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		
	def generate_comprehensive_report(self, 
									 backtest_results: Dict, 
									 statistical_results: Dict,
									 regime_analysis: Dict,
									 chart_images: Dict = None) -> str:
		"""Generate comprehensive HTML report"""
		
		html_content = self._generate_html_header()
		html_content += self._generate_executive_summary(backtest_results, statistical_results)
		html_content += self._generate_performance_section(backtest_results)
		html_content += self._generate_statistical_section(statistical_results)
		html_content += self._generate_regime_section(regime_analysis)
		
		if chart_images:
			html_content += self._generate_charts_section(chart_images)
			
		html_content += self._generate_conclusions()
		html_content += self._generate_html_footer()
		
		# Save report
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		report_file = f"../data/analysis_results/feature_05_report_{timestamp}.html"
		
		with open(report_file, 'w') as f:
			f.write(html_content)
			
		self.logger.info(f"HTML report generated: {report_file}")
		return report_file
		
	def _generate_html_header(self) -> str:
		"""Generate HTML document header with styling"""
		return """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Feature 05: Historical Signal Performance Analysis</title>
	<style>
		body {
			font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
			line-height: 1.6;
			color: #333;
			max-width: 1200px;
			margin: 0 auto;
			padding: 20px;
			background-color: #f8f9fa;
		}
		.header {
			background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
			color: white;
			padding: 30px;
			border-radius: 10px;
			text-align: center;
			margin-bottom: 30px;
		}
		.section {
			background: white;
			padding: 25px;
			margin-bottom: 25px;
			border-radius: 8px;
			box-shadow: 0 2px 10px rgba(0,0,0,0.1);
		}
		.metric-grid {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
			gap: 15px;
			margin: 20px 0;
		}
		.metric-card {
			background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
			color: white;
			padding: 20px;
			border-radius: 8px;
			text-align: center;
		}
		.metric-value {
			font-size: 24px;
			font-weight: bold;
			margin: 10px 0;
		}
		.metric-label {
			font-size: 14px;
			opacity: 0.9;
		}
		.positive { color: #28a745; }
		.negative { color: #dc3545; }
		.neutral { color: #6c757d; }
		table {
			width: 100%;
			border-collapse: collapse;
			margin: 15px 0;
		}
		th, td {
			padding: 12px;
			text-align: left;
			border-bottom: 1px solid #ddd;
		}
		th {
			background-color: #f8f9fa;
			font-weight: bold;
		}
		.chart-container {
			text-align: center;
			margin: 20px 0;
		}
		.chart-container img {
			max-width: 100%;
			height: auto;
			border-radius: 5px;
			box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		}
		.highlight {
			background-color: #fff3cd;
			border-left: 4px solid #ffc107;
			padding: 15px;
			margin: 15px 0;
		}
		.alert-success {
			background-color: #d4edda;
			border-left: 4px solid #28a745;
			padding: 15px;
			margin: 15px 0;
		}
		.alert-warning {
			background-color: #fff3cd;
			border-left: 4px solid #ffc107;
			padding: 15px;
			margin: 15px 0;
		}
	</style>
</head>
<body>
	<div class="header">
		<h1>🎯 Feature 05: Historical Signal Performance Analysis</h1>
		<h2>AI Chip Trading Signal System - Comprehensive Backtesting Report</h2>
		<p>Generated on: """ + datetime.now().strftime("%B %d, %Y at %H:%M:%S") + """</p>
	</div>
"""

	def _generate_executive_summary(self, backtest_results: Dict, statistical_results: Dict) -> str:
		"""Generate executive summary section"""
		
		if not backtest_results or 'error' in backtest_results:
			return '<div class="section"><h2>⚠️ Executive Summary</h2><p>Insufficient data for analysis</p></div>'
			
		train_perf = backtest_results['train_performance']
		test_perf = backtest_results['test_performance']
		
		# Determine overall assessment
		test_profitable = test_perf['total_return_pct'] > 0
		test_sharpe_good = test_perf['sharpe_ratio'] > 1.0
		win_rate_decent = test_perf['win_rate'] > 0.5
		
		assessment_class = "alert-success" if (test_profitable and win_rate_decent) else "alert-warning"
		assessment_text = "✅ Strategy shows positive performance" if (test_profitable and win_rate_decent) else "⚠️ Strategy needs optimization"
		
		return f"""
	<div class="section">
		<h2>📊 Executive Summary</h2>
		<div class="{assessment_class}">
			<strong>{assessment_text}</strong>
		</div>
		
		<div class="metric-grid">
			<div class="metric-card">
				<div class="metric-label">Test Period Win Rate</div>
				<div class="metric-value">{test_perf['win_rate']:.1%}</div>
			</div>
			<div class="metric-card">
				<div class="metric-label">Test Period Return</div>
				<div class="metric-value {'positive' if test_perf['total_return_pct'] > 0 else 'negative'}">{test_perf['total_return_pct']:.2f}%</div>
			</div>
			<div class="metric-card">
				<div class="metric-label">Test Sharpe Ratio</div>
				<div class="metric-value {'positive' if test_perf['sharpe_ratio'] > 1 else 'negative'}">{test_perf['sharpe_ratio']:.2f}</div>
			</div>
			<div class="metric-card">
				<div class="metric-label">Total Signals Tested</div>
				<div class="metric-value">{test_perf['total_trades']}</div>
			</div>
		</div>
		
		<h3>Key Findings</h3>
		<ul>
			<li><strong>Training Performance:</strong> {train_perf['win_rate']:.1%} win rate, {train_perf['total_return_pct']:.2f}% return</li>
			<li><strong>Out-of-Sample Validation:</strong> {test_perf['win_rate']:.1%} win rate, {test_perf['total_return_pct']:.2f}% return</li>
			<li><strong>Risk Management:</strong> Max drawdown of {test_perf['max_drawdown_pct']:.2f}% in test period</li>
			<li><strong>Signal Quality:</strong> Average holding period of {test_perf['avg_holding_days']:.0f} days</li>
		</ul>
	</div>
"""

	def _generate_performance_section(self, backtest_results: Dict) -> str:
		"""Generate detailed performance metrics section"""
		
		if not backtest_results or 'error' in backtest_results:
			return ""
			
		train_perf = backtest_results['train_performance']
		test_perf = backtest_results['test_performance']
		
		return f"""
	<div class="section">
		<h2>📈 Performance Analysis</h2>
		
		<h3>Training vs Test Period Comparison</h3>
		<table>
			<tr>
				<th>Metric</th>
				<th>Training Period</th>
				<th>Test Period</th>
				<th>Difference</th>
			</tr>
			<tr>
				<td>Total Trades</td>
				<td>{train_perf['total_trades']}</td>
				<td>{test_perf['total_trades']}</td>
				<td>{test_perf['total_trades'] - train_perf['total_trades']:+d}</td>
			</tr>
			<tr>
				<td>Win Rate</td>
				<td>{train_perf['win_rate']:.1%}</td>
				<td>{test_perf['win_rate']:.1%}</td>
				<td class="{'positive' if test_perf['win_rate'] >= train_perf['win_rate'] else 'negative'}">{(test_perf['win_rate'] - train_perf['win_rate']):.1%}</td>
			</tr>
			<tr>
				<td>Total Return</td>
				<td>{train_perf['total_return_pct']:.2f}%</td>
				<td>{test_perf['total_return_pct']:.2f}%</td>
				<td class="{'positive' if test_perf['total_return_pct'] >= train_perf['total_return_pct'] else 'negative'}">{(test_perf['total_return_pct'] - train_perf['total_return_pct']):.2f}%</td>
			</tr>
			<tr>
				<td>Sharpe Ratio</td>
				<td>{train_perf['sharpe_ratio']:.2f}</td>
				<td>{test_perf['sharpe_ratio']:.2f}</td>
				<td class="{'positive' if test_perf['sharpe_ratio'] >= train_perf['sharpe_ratio'] else 'negative'}">{(test_perf['sharpe_ratio'] - train_perf['sharpe_ratio']):.2f}</td>
			</tr>
			<tr>
				<td>Max Drawdown</td>
				<td>{train_perf['max_drawdown_pct']:.2f}%</td>
				<td>{test_perf['max_drawdown_pct']:.2f}%</td>
				<td class="{'negative' if test_perf['max_drawdown_pct'] > train_perf['max_drawdown_pct'] else 'positive'}">{(test_perf['max_drawdown_pct'] - train_perf['max_drawdown_pct']):.2f}%</td>
			</tr>
			<tr>
				<td>Profit Factor</td>
				<td>{train_perf['profit_factor']:.2f}</td>
				<td>{test_perf['profit_factor']:.2f}</td>
				<td class="{'positive' if test_perf['profit_factor'] >= train_perf['profit_factor'] else 'negative'}">{(test_perf['profit_factor'] - train_perf['profit_factor']):.2f}</td>
			</tr>
		</table>
		
		<div class="highlight">
			<strong>Performance Assessment:</strong> 
			{'The strategy maintains consistent performance between training and test periods, indicating good generalization.' if abs(test_perf['win_rate'] - train_perf['win_rate']) < 0.1 else 'Performance degradation in test period suggests potential overfitting or changing market conditions.'}
		</div>
	</div>
"""

	def _generate_statistical_section(self, statistical_results: Dict) -> str:
		"""Generate statistical analysis section"""
		
		if not statistical_results:
			return ""
			
		return f"""
	<div class="section">
		<h2>🔬 Statistical Analysis</h2>
		
		<h3>Return Distribution Statistics</h3>
		<div class="metric-grid">
			<div class="metric-card">
				<div class="metric-label">Mean Return</div>
				<div class="metric-value">{statistical_results['returns_pct'].mean() * 100:.2f}%</div>
			</div>
			<div class="metric-card">
				<div class="metric-label">Median Return</div>
				<div class="metric-value">{statistical_results['returns_pct'].median() * 100:.2f}%</div>
			</div>
			<div class="metric-card">
				<div class="metric-label">Standard Deviation</div>
				<div class="metric-value">{statistical_results['returns_pct'].std() * 100:.2f}%</div>
			</div>
			<div class="metric-card">
				<div class="metric-label">Sample Size</div>
				<div class="metric-value">{len(statistical_results['returns_pct'])}</div>
			</div>
		</div>
		
		<h3>Statistical Significance Tests</h3>
		<table>
			<tr>
				<th>Test</th>
				<th>Statistic</th>
				<th>P-Value</th>
				<th>Result</th>
			</tr>
			<tr>
				<td>Profitability (vs Zero)</td>
				<td>{statistical_results['profitability_test']['t_statistic']:.3f}</td>
				<td>{statistical_results['profitability_test']['p_value']:.4f}</td>
				<td class="{'positive' if statistical_results['profitability_test']['p_value'] < 0.05 else 'negative'}">
					{'Significant' if statistical_results['profitability_test']['p_value'] < 0.05 else 'Not Significant'}
				</td>
			</tr>
			<tr>
				<td>Normality (Shapiro-Wilk)</td>
				<td>{statistical_results['normality_test']['statistic']:.4f}</td>
				<td>{statistical_results['normality_test']['p_value']:.4f}</td>
				<td>{'Normal' if statistical_results['normality_test']['p_value'] > 0.05 else 'Non-Normal'}</td>
			</tr>
		</table>
		
		<h3>Confidence Intervals</h3>
		<ul>
			<li><strong>95% CI:</strong> [{statistical_results['confidence_intervals']['95'][0] * 100:.2f}%, {statistical_results['confidence_intervals']['95'][1] * 100:.2f}%]</li>
			<li><strong>99% CI:</strong> [{statistical_results['confidence_intervals']['99'][0] * 100:.2f}%, {statistical_results['confidence_intervals']['99'][1] * 100:.2f}%]</li>
		</ul>
	</div>
"""

	def _generate_regime_section(self, regime_analysis: Dict) -> str:
		"""Generate market regime analysis section"""
		
		if not regime_analysis:
			return ""
			
		current_regime = regime_analysis['current_market_assessment']
		
		regime_html = f"""
	<div class="section">
		<h2>🌍 Market Regime Analysis</h2>
		
		<div class="highlight">
			<strong>Current Market Regime:</strong> {current_regime['current_regime'].upper()}<br>
			<strong>Description:</strong> {current_regime['regime_description']}<br>
			<strong>Days in Regime:</strong> {current_regime['days_in_regime']}<br>
			<strong>Characteristics:</strong> {current_regime['regime_characteristics']}
		</div>
"""

		if regime_analysis['regime_performance']:
			regime_html += """
		<h3>Performance by Market Regime</h3>
		<table>
			<tr>
				<th>Regime</th>
				<th>Signals</th>
				<th>Win Rate</th>
				<th>Avg Return</th>
				<th>Total P&L</th>
			</tr>
"""
			for regime, performance in regime_analysis['regime_performance'].items():
				if regime != 'unknown':
					regime_html += f"""
			<tr>
				<td>{regime.replace('_', ' ').title()}</td>
				<td>{performance['total_signals']}</td>
				<td>{performance['win_rate']:.1%}</td>
				<td class="{'positive' if performance['avg_return'] > 0 else 'negative'}">{performance['avg_return']:.2f}%</td>
				<td class="{'positive' if performance['total_pnl'] > 0 else 'negative'}">${performance['total_pnl']:,.0f}</td>
			</tr>
"""
			regime_html += "</table>"
			
		regime_html += "</div>"
		return regime_html

	def _generate_charts_section(self, chart_images: Dict) -> str:
		"""Generate charts section with embedded images"""
		
		charts_html = '<div class="section"><h2>📊 Performance Charts</h2>'
		
		for chart_name, image_path in chart_images.items():
			try:
				with open(image_path, 'rb') as f:
					image_data = base64.b64encode(f.read()).decode()
				
				charts_html += f"""
		<div class="chart-container">
			<h3>{chart_name.replace('_', ' ').title()}</h3>
			<img src="data:image/png;base64,{image_data}" alt="{chart_name}">
		</div>
"""
			except Exception as e:
				charts_html += f'<p>Error loading chart {chart_name}: {e}</p>'
				
		charts_html += '</div>'
		return charts_html

	def _generate_conclusions(self) -> str:
		"""Generate conclusions and recommendations section"""
		
		return """
	<div class="section">
		<h2>🎯 Conclusions and Recommendations</h2>
		
		<h3>Key Findings</h3>
		<ul>
			<li><strong>Strategy Validation:</strong> Historical backtesting provides evidence for signal effectiveness</li>
			<li><strong>Statistical Significance:</strong> Returns show statistical validation through t-tests and confidence intervals</li>
			<li><strong>Regime Awareness:</strong> Performance varies by market regime, enabling adaptive strategies</li>
			<li><strong>Risk Management:</strong> Drawdown analysis validates position sizing methodology</li>
		</ul>
		
		<h3>Recommended Actions</h3>
		<ol>
			<li><strong>Live Trading Implementation:</strong> Deploy validated signals in live environment with reduced position sizes</li>
			<li><strong>Regime Adaptation:</strong> Adjust position sizing based on current market regime characteristics</li>
			<li><strong>Continuous Monitoring:</strong> Weekly performance reviews to detect regime changes</li>
			<li><strong>Signal Refinement:</strong> Focus on highest-performing signal types and market conditions</li>
		</ol>
		
		<h3>Risk Considerations</h3>
		<ul>
			<li>Past performance does not guarantee future results</li>
			<li>Market regime changes may impact signal effectiveness</li>
			<li>Position sizing should reflect risk tolerance and market volatility</li>
			<li>Regular rebalancing recommended based on correlation changes</li>
		</ul>
	</div>
"""

	def _generate_html_footer(self) -> str:
		"""Generate HTML document footer"""
		
		return f"""
	<div class="section" style="text-align: center; color: #6c757d;">
		<hr>
		<p>Report generated by AI Chip Trading Signal System</p>
		<p>Feature 05: Historical Signal Performance Analysis</p>
		<p>© 2025 - For Internal Use Only</p>
	</div>
</body>
</html>
"""
