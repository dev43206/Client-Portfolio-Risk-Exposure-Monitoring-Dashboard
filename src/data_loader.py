import random
import time

import pandas as pd
import yfinance as yf

MAX_RETRIES = 3


def load_prices(tickers, start, end):
    """Download adjusted close prices for one or more tickers.

    Retries the download up to MAX_RETRIES times if yfinance returns no
    data or raises an error, which helps with transient network issues
    (e.g. on cloud deployments). Returns a DataFrame indexed by date with
    one column per ticker.
    """
    if isinstance(tickers, str):
        tickers = [t.strip() for t in tickers.split(",") if t.strip()]

    data = None
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                group_by="column",
            )
        except Exception as exc:
            last_error = exc
            data = None

        if data is not None and not data.empty:
            break

        if attempt < MAX_RETRIES:
            time.sleep(random.uniform(1.0, 2.0))

    if data is None or data.empty:
        if last_error is not None:
            raise ValueError(
                f"No price data returned for the given tickers/date range "
                f"after {MAX_RETRIES} attempts: {last_error}"
            )
        raise ValueError(f"No price data returned for the given tickers/date range after {MAX_RETRIES} attempts.")

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        # Single ticker: columns are flat (Open, High, Low, Close, Volume)
        prices = data[["Close"]]
        prices.columns = tickers

    prices = prices.dropna(axis=1, how="all")  # drop tickers with no data at all
    prices = prices.dropna(how="all").ffill().dropna()

    if prices.empty:
        raise ValueError("Price data is empty after cleaning missing values.")

    return prices