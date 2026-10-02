"""Load client and position data from the local SQLite database."""

import pandas as pd
from database.queries import get_all_clients, get_all_positions


def load_sample_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return database clients and positions as independent DataFrames."""
    clients = pd.DataFrame(get_all_clients(), columns=["client_id", "client_name", "risk_profile", "credit_limit"])
    positions = pd.DataFrame(get_all_positions(), columns=["position_id", "client_id", "instrument", "symbol", "quantity", "price", "market_value"])
    return clients, positions
