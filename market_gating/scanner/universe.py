"""S&P 500 Universe Loader
==========================
Scrapes the current S&P 500 constituent list from Wikipedia and caches the
result for 24 hours.  Tickers are normalised so that dots are replaced with
hyphens (e.g. ``BRK.B`` → ``BRK-B``) for yfinance compatibility.
"""

from __future__ import annotations

import logging
import time

import pandas as pd

logger = logging.getLogger(__name__)

_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Module-level cache --------------------------------------------------------
_cached_tickers: list[str] | None = None
_cached_at: float = 0.0


def get_sp500_tickers(*, force_refresh: bool = False) -> list[str]:
    """Return a sorted list of current S&P 500 ticker symbols.

    Parameters
    ----------
    force_refresh : bool
        If *True*, bypass the cache and re-scrape.

    Returns
    -------
    list[str]
        Sorted ticker strings, dot-normalised for yfinance.
    """
    global _cached_tickers, _cached_at

    now = time.time()
    if (
        not force_refresh
        and _cached_tickers is not None
        and (now - _cached_at) < _CACHE_TTL_SECONDS
    ):
        return list(_cached_tickers)

    logger.info("Fetching S&P 500 constituents from Wikipedia…")
    try:
        tables = pd.read_html(_WIKI_URL, header=0)
    except Exception:
        logger.exception("Failed to fetch S&P 500 list from Wikipedia")
        if _cached_tickers is not None:
            logger.warning("Returning stale cached tickers")
            return list(_cached_tickers)
        raise

    # The first table on the page contains the constituents.
    df = tables[0]
    raw_tickers: pd.Series = df["Symbol"].astype(str).str.strip()

    # Replace dots with hyphens for yfinance (e.g. BRK.B → BRK-B).
    tickers = sorted(raw_tickers.str.replace(".", "-", regex=False).tolist())

    _cached_tickers = tickers
    _cached_at = now
    logger.info("Cached %d S&P 500 tickers", len(tickers))

    return list(tickers)
