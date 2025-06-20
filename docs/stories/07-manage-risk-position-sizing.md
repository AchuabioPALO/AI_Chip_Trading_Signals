# User Story: 7 - Manage Risk and Position Sizing

## Persona: Robert (Portfolio Manager, 10+ years)
**Background:** Senior portfolio manager overseeing $1B+ in tech-focused strategies. Specializes in risk-adjusted return optimization and systematic position sizing across volatile growth sectors.

---

## Story: Automated Risk Management and Position Optimization

**As a** portfolio manager,
**I want** automated position sizing recommendations based on volatility conditions,
**so that** I can optimize risk-adjusted returns while avoiding oversized positions during stress periods.

## Acceptance Criteria

- [x] Volatility-adjusted position sizing: 2% during low-VIX periods, 0.5% during crisis periods
- [x] Automatic risk management integration with signal generation
- [x] Position sizing recommendations for each signal strength level
- [x] Stop loss recommendations based on historical drawdown patterns
- [x] Real-time volatility monitoring and position size recalibration
- [x] Risk management alerts when correlation quality degrades below 0.3
- [x] Integration with existing portfolio management systems

## User Journey:

1. Robert reviews morning position sizing recommendations based on overnight volatility
2. Analyzes risk-adjusted position suggestions for new NVDA signal (strength 8/10)
3. Checks portfolio-level exposure limits and concentration risk metrics
4. Implements suggested 2.5% position with automated stop-loss at 5%
5. Monitors real-time position size adjustments as volatility changes
6. Receives alerts when 60-day correlation degrades, triggering position review
7. Documents risk management decisions for monthly performance attribution

## Success Metrics:

- Maximum 3% individual position size regardless of signal strength
- Portfolio drawdown limited to <10% during any 30-day period
- 1.5+ Sharpe ratio maintained through automated position sizing
- 95% compliance with risk management rules and position limits
- Zero manual overrides required for position sizing calculations

## Technical Requirements:

- Real-time volatility calculation using 20-day realized volatility measures
- Position sizing algorithms incorporating VIX levels and sector concentration
- Integration APIs with existing portfolio management and execution systems
- Automated stop-loss order generation and monitoring capabilities
- Risk monitoring dashboard with real-time exposure and correlation tracking
- Historical drawdown analysis for stop-loss calibration and optimization

## Pain Points Addressed:

- Manual position sizing decisions leading to inconsistent risk management
- Oversized positions during volatile periods causing excessive portfolio drawdowns
- Lack of systematic approach to stop-loss placement and risk controls
- Time-consuming integration between signal generation and portfolio management
- Reactive risk management instead of proactive position sizing optimization
