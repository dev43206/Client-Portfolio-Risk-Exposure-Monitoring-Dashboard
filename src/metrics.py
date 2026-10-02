import numpy as np
import pandas as pd

TRADING_DAYS = 252


def daily_returns(prices):
    return prices.pct_change().dropna()


def cumulative_returns(returns):
    return (1 + returns).cumprod() - 1


def annualised_volatility(returns):
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns, rf=0.0):
    annual_return = returns.mean() * TRADING_DAYS
    annual_vol = annualised_volatility(returns)
    return (annual_return - rf) / annual_vol


def historical_var(returns, confidence=0.95):
    """Historical Value at Risk, returned as a positive loss figure."""
    percentile = (1 - confidence) * 100
    var = np.percentile(returns, percentile)
    return -var


def drawdown_series(returns):
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    return cum / running_max - 1


def max_drawdown(returns):
    return drawdown_series(returns).min()


def portfolio_returns(returns, weights):
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()
    return returns.dot(weights)


def rolling_volatility(returns, window=63):
    return returns.rolling(window).std() * np.sqrt(TRADING_DAYS)


def rolling_sharpe(returns, window=63, rf=0.0):
    rolling_mean = returns.rolling(window).mean() * TRADING_DAYS
    rolling_vol = rolling_volatility(returns, window=window)
    return (rolling_mean - rf) / rolling_vol


def beta(returns, benchmark_returns):
    covariance = returns.cov(benchmark_returns)
    benchmark_variance = benchmark_returns.var()
    return covariance / benchmark_variance


def alpha(returns, benchmark_returns, rf=0.0):
    portfolio_annual_return = returns.mean() * TRADING_DAYS
    benchmark_annual_return = benchmark_returns.mean() * TRADING_DAYS
    b = beta(returns, benchmark_returns)
    return (portfolio_annual_return - rf) - b * (benchmark_annual_return - rf)


def risk_contribution(returns, weights):
    """Annualised risk contribution of each asset to total portfolio volatility.

    Sums to the portfolio's annualised volatility (sqrt(252)-scaled).
    """
    clean_returns = returns.dropna()
    weights_arr = np.array(weights, dtype=float)
    weights_arr = weights_arr / weights_arr.sum()

    cov_matrix = clean_returns.cov().values
    portfolio_variance = weights_arr @ cov_matrix @ weights_arr
    portfolio_vol = np.sqrt(max(portfolio_variance, 0.0))

    if portfolio_vol == 0 or np.isnan(portfolio_vol):
        contributions = np.zeros_like(weights_arr)
    else:
        marginal_contribution = cov_matrix @ weights_arr / portfolio_vol
        contributions = weights_arr * marginal_contribution

    return pd.Series(contributions * np.sqrt(TRADING_DAYS), index=clean_returns.columns)


def stress_test(returns, weights, scenarios):
    """Portfolio total return over each historical scenario window.

    `scenarios` maps a scenario name to a (start_date, end_date) string tuple.
    Scenarios with no overlapping data are returned as None.
    """
    results = {}
    for name, (start, end) in scenarios.items():
        window = returns.loc[start:end]
        if window.empty:
            results[name] = None
            continue

        port_window_returns = portfolio_returns(window, weights)
        if port_window_returns.empty:
            results[name] = None
            continue

        cumulative = (1 + port_window_returns).cumprod()
        results[name] = cumulative.iloc[-1] - 1

    return results


def monte_carlo_simulation(returns, weights, n_simulations=1000, n_days=252, seed=42):
    """Simulate future portfolio value paths via geometric random walk.

    Daily returns are drawn from a Normal distribution fitted to the
    portfolio's historical mean and standard deviation. Returns a
    DataFrame of shape (n_days, n_simulations), each path starting near 1.0.
    """
    port_ret = portfolio_returns(returns, weights).dropna()

    if port_ret.empty:
        raise ValueError("Not enough return history to run a Monte Carlo simulation.")

    mu = port_ret.mean()
    sigma = port_ret.std()
    if np.isnan(sigma):
        sigma = 0.0

    rng = np.random.default_rng(seed)
    simulated_daily_returns = rng.normal(loc=mu, scale=sigma, size=(n_days, n_simulations))
    paths = np.cumprod(1 + simulated_daily_returns, axis=0)

    columns = [f"sim_{i + 1}" for i in range(n_simulations)]
    return pd.DataFrame(paths, index=range(1, n_days + 1), columns=columns)


def efficient_frontier(returns, n_portfolios=5000, rf=0.0, seed=42):
    """Monte Carlo search over random long-only portfolio weights.

    Returns (frontier_df, max_sharpe_portfolio, min_vol_portfolio):
      - frontier_df: one row per simulated portfolio, with columns
        "return", "volatility", "sharpe", and "weight_<ticker>" per asset.
      - max_sharpe_portfolio / min_vol_portfolio: the best rows as Series.

    With a single asset, every portfolio is the same point (weight=1.0).
    """
    clean_returns = returns.dropna()
    tickers = list(clean_returns.columns)
    n_assets = len(tickers)

    if clean_returns.empty or n_assets == 0:
        raise ValueError("No return history available to build an efficient frontier.")

    mean_returns = clean_returns.mean().values * TRADING_DAYS
    cov_matrix = clean_returns.cov().values * TRADING_DAYS

    if n_assets == 1:
        weights_matrix = np.ones((1, 1))
    else:
        rng = np.random.default_rng(seed)
        weights_matrix = rng.dirichlet(np.ones(n_assets), size=n_portfolios)

    portfolio_return_arr = weights_matrix @ mean_returns
    portfolio_vol_arr = np.sqrt(np.einsum("ij,jk,ik->i", weights_matrix, cov_matrix, weights_matrix))
    sharpe_arr = np.divide(
        portfolio_return_arr - rf,
        portfolio_vol_arr,
        out=np.zeros_like(portfolio_return_arr),
        where=portfolio_vol_arr != 0,
    )

    data = {
        "return": portfolio_return_arr,
        "volatility": portfolio_vol_arr,
        "sharpe": sharpe_arr,
    }
    for i, ticker in enumerate(tickers):
        data[f"weight_{ticker}"] = weights_matrix[:, i]

    frontier_df = pd.DataFrame(data)

    max_sharpe_portfolio = frontier_df.loc[frontier_df["sharpe"].idxmax()]
    min_vol_portfolio = frontier_df.loc[frontier_df["volatility"].idxmin()]

    return frontier_df, max_sharpe_portfolio, min_vol_portfolio