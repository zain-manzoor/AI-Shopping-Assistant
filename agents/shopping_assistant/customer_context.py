"""Map an ADK-owned session identifier to a stable local demo customer ID."""

from __future__ import annotations

import hashlib

from shopping_data.cart import ensure_customer
from shopping_data.database import open_database


def customer_id_for_session(session_id: str) -> str:
    """Create a stable, opaque demo identity from the host-created session ID."""
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("An application-created session ID is required.")
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]
    customer_id = f"demo-{digest}"
    with open_database() as connection:
        ensure_customer(connection, customer_id)
    return customer_id


def inject_customer_identity(args: dict[str, object], session_id: str) -> str:
    """Overwrite any caller-supplied identity using the host-created ADK session."""
    customer_id = customer_id_for_session(session_id)
    args["customer_id"] = customer_id
    return customer_id
