"""Simple and explicit client-level exposure calculations."""

import math
from collections.abc import Iterable

import pandas as pd

from .risk import classify_utilization_risk


def _number(value: object, default: float = 0.0) -> float:
    """Convert a value to a finite float, falling back for invalid/missing input."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def calculate_client_exposure(positions: pd.DataFrame) -> pd.Series:
    """Sum valid supplied market values by client; exposure floors totals at zero."""
    required = {"client_id", "market_value"}
    if not required.issubset(positions.columns):
        return pd.Series(dtype="float64", name="current_exposure")
    values = positions["market_value"].map(_number)
    totals = values.groupby(positions["client_id"]).sum()
    totals = totals.clip(lower=0.0)
    totals.name = "current_exposure"
    return totals


def calculate_credit_utilization(current_exposure: float, credit_limit: float) -> float:
    """Return exposure divided by a positive limit as a percentage; otherwise 0."""
    limit = _number(credit_limit)
    if limit <= 0:
        return 0.0
    return _number(current_exposure) / limit * 100.0


def calculate_available_credit(credit_limit: float, current_exposure: float) -> float:
    """Return credit limit less current exposure."""
    return _number(credit_limit) - _number(current_exposure)


def generate_client_exposure_summary(
    clients: pd.DataFrame, positions: pd.DataFrame
) -> pd.DataFrame:
    """Build one exposure, utilization, and risk row per client."""
    required = {"client_id", "client_name", "credit_limit", "risk_profile"}
    if not required.issubset(clients.columns):
        return pd.DataFrame(columns=["client_id", "client_name", "credit_limit", "risk_profile", "exposure", "utilization", "risk_status"])
    exposures = calculate_client_exposure(positions)
    result = clients.copy()
    result["credit_limit"] = result["credit_limit"].map(_number)
    result["exposure"] = result["client_id"].map(exposures).fillna(0.0)
    result["utilization"] = result.apply(
        lambda row: calculate_credit_utilization(row["exposure"], row["credit_limit"]), axis=1
    )
    result["risk_status"] = result["utilization"].map(classify_utilization_risk)
    return result
