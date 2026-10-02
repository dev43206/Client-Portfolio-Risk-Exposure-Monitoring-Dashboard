"""Deterministic sample data for the demonstration dashboard."""

import pandas as pd


def load_sample_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return sample clients and positions as independent DataFrames."""
    clients = pd.DataFrame(
        [
            ("C001", "ABC Capital", 1_000_000.0, "Conservative"),
            ("C002", "XYZ Investments", 750_000.0, "Moderate"),
            ("C003", "PQR Fund", 500_000.0, "Aggressive"),
            ("C004", "Global Alpha", 1_500_000.0, "Moderate"),
        ],
        columns=["client_id", "client_name", "credit_limit", "risk_profile"],
    )
    positions = pd.DataFrame(
        [
            ("C001", "Equity", 1200, 250, 300000), ("C001", "Bond", 500, 600, 300000),
            ("C001", "FX", 100000, 1.1, 110000), ("C002", "Equity", 800, 400, 320000),
            ("C002", "Option", 100, 1500, 150000), ("C002", "Bond", 400, 250, 100000),
            ("C003", "Equity", 900, 300, 270000), ("C003", "IRS", 1, 90000, 90000),
            ("C003", "FX", 50000, 1.2, 60000), ("C004", "Bond", 1500, 500, 750000),
            ("C004", "Equity", 1000, 450, 450000), ("C004", "IRS", 1, 200000, 200000),
        ],
        columns=["client_id", "instrument", "quantity", "price", "market_value"],
    )
    return clients, positions
