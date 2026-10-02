# Client exposure database

This module stores the educational dashboard's client, position, and exposure snapshot data in SQLite at `data/risk_dashboard.db`. It uses Python's standard library and creates the database directory and tables automatically when a connection is opened.

From the project root, initialize and seed the demonstration data with:

```powershell
python -m database.seed
```

The script uses stable IDs and `INSERT OR IGNORE`, so rerunning it does not duplicate seeded rows. The query module provides client/position retrieval, portfolio market value aggregation, snapshot insertion, and exposure history. Seeded position prices and market values are educational inputs, not live valuations.
