"""Parameterized queries for client exposure persistence."""

from datetime import datetime

from .connection import connection_context


def get_all_clients() -> list[dict]:
    with connection_context() as connection:
        rows = connection.execute(
            "SELECT client_id, client_name, risk_profile, credit_limit FROM clients ORDER BY client_id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_client_by_id(client_id: int) -> dict | None:
    with connection_context() as connection:
        row = connection.execute(
            "SELECT client_id, client_name, risk_profile, credit_limit FROM clients WHERE client_id = ?",
            (client_id,),
        ).fetchone()
    return dict(row) if row else None


def get_client_positions(client_id: int) -> list[dict]:
    with connection_context() as connection:
        rows = connection.execute(
            "SELECT position_id, client_id, instrument, symbol, quantity, price, market_value "
            "FROM positions WHERE client_id = ? ORDER BY position_id",
            (client_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_positions() -> list[dict]:
    with connection_context() as connection:
        rows = connection.execute(
            "SELECT position_id, client_id, instrument, symbol, quantity, price, market_value "
            "FROM positions ORDER BY client_id, position_id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_client_portfolio_values() -> list[dict]:
    with connection_context() as connection:
        rows = connection.execute(
            "SELECT c.client_id, c.client_name, c.credit_limit, "
            "COALESCE(SUM(p.market_value), 0) AS portfolio_value "
            "FROM clients AS c LEFT JOIN positions AS p ON c.client_id = p.client_id "
            "GROUP BY c.client_id, c.client_name, c.credit_limit ORDER BY c.client_id"
        ).fetchall()
    return [dict(row) for row in rows]


def save_exposure_snapshot(
    client_id: int,
    current_exposure: float,
    credit_limit: float,
    utilization: float,
    risk_status: str,
    snapshot_date: str | None = None,
) -> int:
    timestamp = snapshot_date or datetime.now().astimezone().isoformat(timespec="seconds")
    with connection_context() as connection:
        cursor = connection.execute(
            "INSERT INTO exposure_snapshots "
            "(client_id, current_exposure, credit_limit, utilization, risk_status, snapshot_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (client_id, current_exposure, credit_limit, utilization, risk_status, timestamp),
        )
        return int(cursor.lastrowid)


def get_exposure_history(client_id: int) -> list[dict]:
    with connection_context() as connection:
        rows = connection.execute(
            "SELECT snapshot_id, client_id, current_exposure, credit_limit, utilization, risk_status, snapshot_date "
            "FROM exposure_snapshots WHERE client_id = ? ORDER BY snapshot_date DESC, snapshot_id DESC",
            (client_id,),
        ).fetchall()
    return [dict(row) for row in rows]
