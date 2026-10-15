"""ADK Web-discoverable shopping assistant package."""

__all__ = ["root_agent"]


def __getattr__(name: str):
    """Load the ADK agent only when the ADK loader requests its root export."""
    if name == "root_agent":
        from .agent import root_agent

        return root_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
