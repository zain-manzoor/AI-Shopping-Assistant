"""Pure helpers for session-local recommendation context."""

from __future__ import annotations

from typing import Any

PREFERENCE_KEYS = {
    "budget_pkr",
    "intended_use",
    "category",
    "preferred_features",
    "required_features",
    "brand",
    "color",
    "size",
    "material",
    "fit",
}


def remember_preferences(state: Any, preferences: dict[str, str]) -> dict[str, str]:
    """Merge supported shopping criteria into one ADK conversation's state."""
    current = dict(state.get("recommendation_preferences", {}))
    for key, value in preferences.items():
        normalized_key = key.strip().casefold()
        if normalized_key in PREFERENCE_KEYS and isinstance(value, str) and value.strip():
            current[normalized_key] = value.strip()[:160]
    state["recommendation_preferences"] = current
    return current


def remember_product(state: Any, state_key: str, product_id: str) -> list[str]:
    """Add one product ID to a conversation-local exclusion set."""
    if state_key not in {"rejected_product_ids", "owned_product_ids"}:
        raise ValueError("Unsupported conversation state key.")
    if not isinstance(product_id, str) or not product_id.strip():
        raise ValueError("A product ID is required.")
    products = set(state.get(state_key, []))
    products.add(product_id.strip()[:64])
    state[state_key] = sorted(products)
    return state[state_key]


def recommendation_memory(state: Any) -> dict[str, Any]:
    """Return only this conversation's stored criteria and exclusions."""
    return {
        "preferences": state.get("recommendation_preferences", {}),
        "rejected_product_ids": state.get("rejected_product_ids", []),
        "owned_product_ids": state.get("owned_product_ids", []),
    }
