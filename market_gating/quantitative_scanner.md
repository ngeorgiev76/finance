Build a quantitative stock scanner that only activates when the macro gate gives the green light. Scans a universe and ranks by multi-factor score.

Universe: S&P 500 constituents. Download daily OHLCV via yfinance, 1yr lookback.

5 Scanner Factors (each scored 0-100, percentile rank across universe):

Momentum Crossover: 10-day EMA crossed above 50-day EMA in last 5 days? Score based on gap size + 3-month return magnitude.

Volume Surge: 5-day avg volume / 20-day avg volume. Expanding volume = institutions accumulating. Map 0.7 -> 0, 2.0 -> 100.

Relative Strength vs SPY: 20-day stock return minus 20-day SPY return. Outperforming market = higher score. Percentile rank the spread.

52-Week High Proximity: current price / 52-week high. Above 0.95 scores highest. Documented academic signal (George & Hwang 2004).

Short Interest Decline: change in short interest vs prior period. Declining short interest = shorts covering = bullish = higher score.

Composite: equal weight all 5. In REDUCED mode: only surface stocks above 75. In DEFENSIVE mode: scanner disabled, return empty list.

Entry: run_scanner.py  Dashboard: add as Page 2 in Streamlit app.