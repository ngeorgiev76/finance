Build a Claude API analyst layer that scores each scanner candidate on fundamental quality. This is the nondeterministic layer.

Use Anthropic SDK. API key from .env as ANTHROPIC_API_KEY.

Candidate Analyzer (analyst/analyzer.py):
For each candidate, gather last 4 quarters from yfinance: revenue, net income, operating cash flow, FCF, gross margin, operating margin, debt/equity, ROE. Calculate CFO/NI ratio and AR growth vs revenue growth.

Send to Claude with system prompt: "You are a senior equity research analyst. Score 1-10 on: Earnings Quality, Growth Trajectory, Balance Sheet Health, Margin Trends, Red Flags." Output as JSON.

Cache results in SQLite by (ticker, quarter_end). Same quarter = free.

Score Blender (analyst/blender.py):
60% quantitative composite (from scanner) + 40% Claude fundamental score.
Re-rank candidates by blended score. Flag any candidate where rank changed by 3+ positions (green glow if upgraded, red glow if downgraded).

These flagged rank changes are the key insight: where the quant model and the AI analyst disagree is where the most interesting information lives.

Entry: run_analysis.py --scan-and-analyze (full end-to-end)
Dashboard: add as Page 3 with blended table, rank deltas, expandable analysis.