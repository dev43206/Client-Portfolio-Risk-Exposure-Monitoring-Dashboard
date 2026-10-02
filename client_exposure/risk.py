"""Transparent educational utilization risk bands."""

import math


def classify_utilization_risk(utilization: float) -> str:
    """Classify utilization percentage using the stated simplified thresholds."""
    try:
        value = float(utilization)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if not math.isfinite(value):
        return "UNKNOWN"
    if value < 50:
        return "LOW"
    if value < 80:
        return "MEDIUM"
    if value < 100:
        return "HIGH"
    return "BREACH"
