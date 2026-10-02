import numpy as np
from scipy.optimize import minimize

TRADING_DAYS = 252


def _compute_stats(weights, mean_returns, cov_matrix, rf=0.0):
    ret = float(weights @ mean_returns)
    vol = float(np.sqrt(max(float(weights @ cov_matrix @ weights), 0.0)))
    sharpe = (ret - rf) / vol if vol > 0 else 0.0
    return ret, vol, sharpe


def optimize_max_sharpe(returns, rf=0.0):
    """Find weights maximizing Sharpe ratio (long-only, weights sum to 1).

    Returns (weights_array, annual_return, annual_vol, sharpe).
    Single-asset portfolios return weight=[1.0] without running the solver.
    """
    clean = returns.dropna()
    n = clean.shape[1]
    mean_ret = clean.mean().values * TRADING_DAYS
    cov = clean.cov().values * TRADING_DAYS

    if n == 1:
        ret, vol, sharpe = _compute_stats(np.array([1.0]), mean_ret, cov, rf)
        return np.array([1.0]), ret, vol, sharpe

    def neg_sharpe(w):
        r = float(w @ mean_ret)
        v = float(np.sqrt(max(float(w @ cov @ w), 0.0)))
        return -(r - rf) / v if v > 0 else 0.0

    w0 = np.ones(n) / n
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0.0, 1.0)] * n

    result = minimize(
        neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 1000},
    )

    w = np.clip(result.x, 0.0, 1.0)
    w /= w.sum()
    ret, vol, sharpe = _compute_stats(w, mean_ret, cov, rf)
    return w, ret, vol, sharpe


def optimize_min_volatility(returns, rf=0.0):
    """Find weights minimizing annualized volatility (long-only, weights sum to 1).

    Returns (weights_array, annual_return, annual_vol, sharpe).
    Single-asset portfolios return weight=[1.0] without running the solver.
    """
    clean = returns.dropna()
    n = clean.shape[1]
    mean_ret = clean.mean().values * TRADING_DAYS
    cov = clean.cov().values * TRADING_DAYS

    if n == 1:
        ret, vol, sharpe = _compute_stats(np.array([1.0]), mean_ret, cov, rf)
        return np.array([1.0]), ret, vol, sharpe

    def portfolio_vol(w):
        return float(np.sqrt(max(float(w @ cov @ w), 0.0)))

    w0 = np.ones(n) / n
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0.0, 1.0)] * n

    result = minimize(
        portfolio_vol, w0, method="SLSQP", bounds=bounds, constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 1000},
    )

    w = np.clip(result.x, 0.0, 1.0)
    w /= w.sum()
    ret, vol, sharpe = _compute_stats(w, mean_ret, cov, rf)
    return w, ret, vol, sharpe