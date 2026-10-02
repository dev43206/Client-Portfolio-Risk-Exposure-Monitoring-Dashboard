"""Insert the repeatable educational demonstration dataset."""

from .connection import connection_context

CLIENTS = [
    (1, "ABC Capital", "Conservative", 1_000_000.0),
    (2, "XYZ Investments", "Moderate", 750_000.0),
    (3, "PQR Fund", "Aggressive", 500_000.0),
    (4, "Global Alpha", "Moderate", 1_500_000.0),
]

POSITIONS = [
    (1, 1, "Equity", "ABC", 1200, 250, 300000),
    (2, 1, "Bond", "UST10Y", 500, 600, 300000),
    (3, 1, "FX", "EURUSD", 100000, 1.1, 110000),
    (4, 2, "Equity", "XYZ", 800, 400, 320000),
    (5, 2, "Option", "XYZ-C", 100, 1500, 150000),
    (6, 2, "Bond", "CORP5Y", 400, 250, 100000),
    (7, 3, "Equity", "PQR", 900, 300, 270000),
    (8, 3, "IRS", "USD-SWAP", 1, 90000, 90000),
    (9, 3, "FX", "GBPUSD", 50000, 1.2, 60000),
    (10, 4, "Bond", "UST5Y", 1500, 500, 750000),
    (11, 4, "Equity", "GLBA", 1000, 450, 450000),
    (12, 4, "IRS", "EUR-SWAP", 1, 200000, 200000),
]


def seed_database() -> None:
    with connection_context() as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO clients (client_id, client_name, risk_profile, credit_limit) "
            "VALUES (?, ?, ?, ?)",
            CLIENTS,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO positions "
            "(position_id, client_id, instrument, symbol, quantity, price, market_value) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            POSITIONS,
        )


if __name__ == "__main__":
    seed_database()
    print("Database initialized and demonstration data seeded.")
