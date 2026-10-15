"""Session-local preferences, rejection, and ownership memory tests."""

from __future__ import annotations

import unittest

from agents.shopping_assistant.conversation_state import (
    recommendation_memory,
    remember_preferences,
    remember_product,
)


class ConversationStateTests(unittest.TestCase):
    def test_preferences_merge_only_allowed_keys_and_stay_in_given_state(self) -> None:
        first_session: dict = {}
        second_session: dict = {}
        remember_preferences(first_session, {"budget_pkr": "50000", "favorite_movie": "..."})
        self.assertEqual(first_session["recommendation_preferences"], {"budget_pkr": "50000"})
        self.assertEqual(recommendation_memory(second_session)["preferences"], {})

    def test_rejected_and_owned_products_are_unique_session_local_ids(self) -> None:
        state: dict = {}
        self.assertEqual(remember_product(state, "rejected_product_ids", "EL-001"), ["EL-001"])
        self.assertEqual(remember_product(state, "rejected_product_ids", "EL-001"), ["EL-001"])
        self.assertEqual(remember_product(state, "owned_product_ids", "BK-001"), ["BK-001"])
        self.assertEqual(recommendation_memory(state)["owned_product_ids"], ["BK-001"])

    def test_invalid_product_and_state_fields_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            remember_product({}, "cart", "EL-001")
        with self.assertRaises(ValueError):
            remember_product({}, "owned_product_ids", " ")
