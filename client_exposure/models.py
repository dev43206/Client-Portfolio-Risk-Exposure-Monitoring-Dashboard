"""Data structures for client exposure monitoring."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Client:
    """A client and its assigned credit limit and classification."""

    client_id: str
    client_name: str
    credit_limit: float
    risk_profile: str


@dataclass(frozen=True)
class Position:
    """A position with supplied market value; no instrument pricing is performed."""

    client_id: str
    instrument: str
    quantity: float
    price: float
    market_value: float
