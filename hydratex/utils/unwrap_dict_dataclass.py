from collections.abc import Mapping


def unwrap_single[T](items: Mapping[str, T], label: str = "item") -> T:
    """Return the single value from a one-entry mapping, or raise ValueError."""
    if len(items) != 1:
        raise ValueError(f"Expected 1 {label}, got {len(items)}.")
    return next(iter(items.values()))