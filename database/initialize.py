"""Initialize the dashboard database with demonstration data when it is empty."""

from .queries import get_all_clients
from .seed import seed_database


def initialize_database() -> None:
    """Create the schema and seed clients only when no client data exists."""
    if not get_all_clients():
        seed_database()
