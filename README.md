# BiasGuard

An event-driven backtesting engine for Python, built around one idea:
**a backtest is only useful if you can trust it.** BiasGuard simulates execution
with realistic costs and (roadmap) automatically checks strategies for lookahead
bias, overfitting and cost fragility.

> Status: early development (Week 1: core engine). Not investment advice. Results
> on synthetic data say nothing about real-world profitability.

## Why another backtester?
Existing tools focus on running strategies. BiasGuard focuses on *validating the
backtest itself*.

## Design principles
- **Structural lookahead protection:** strategies only see data via `latest_bars`,
  which never returns bars after the current timestamp.
- **Decide on close, fill on next open:** an order can never execute at a price
  used to make the decision.
- **Deterministic:** same data + same strategy = identical results.
- **Costs are first-class:** commission and slippage are part of every run.

## Quick start
```bash
pip install -e ".[dev]"
pytest
python examples/run_baseline.py
```

## Roadmap
- [x] Event loop, data handler, portfolio, simulated execution, core metrics
- [ ] Order types (limit/stop), partial fills, margin and leverage rules
- [ ] Sortino, VaR/CVaR, turnover, rolling stats
- [ ] Lookahead detector (truncated-data replay)
- [ ] Walk-forward and purged k-fold validation
- [ ] Cost-stress and parameter-sensitivity checks, deflated Sharpe
- [ ] CLI (YAML configs) and HTML/Markdown reports
