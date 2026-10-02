CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY,
    client_name TEXT NOT NULL,
    risk_profile TEXT NOT NULL,
    credit_limit REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    position_id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    instrument TEXT NOT NULL,
    symbol TEXT,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    market_value REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE TABLE IF NOT EXISTS exposure_snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    current_exposure REAL NOT NULL,
    credit_limit REAL NOT NULL,
    utilization REAL NOT NULL,
    risk_status TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
