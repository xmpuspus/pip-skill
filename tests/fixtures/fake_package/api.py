"""Public API functions with various annotation patterns."""


def fetch(url: str, timeout: int = 30, headers: dict | None = None) -> dict:
    """Fetch data from a URL.

    Args:
        url: The URL to fetch from.
        timeout: Request timeout in seconds.
        headers: Optional HTTP headers.

    Returns:
        Response data as a dictionary.

    Example:
        >>> fetch("https://api.example.com/data")
        {'status': 'ok'}
    """
    return {"url": url, "timeout": timeout}


def create_item(name: str, value: int, tags: list[str] | None = None) -> dict:
    """Create a new item.

    Args:
        name: Item name.
        value: Item value.
        tags: Optional tags for the item.

    Returns:
        The created item.
    """
    return {"name": name, "value": value, "tags": tags or []}


def process(data):
    """Process data without type annotations.

    Args:
        data: The data to process. Can be a dict or list.

    Returns:
        Processed result.
    """
    return data


def _internal_helper():
    """Should not be included in public API."""
    pass


def deprecated_func():
    """This function is deprecated. Use fetch() instead."""
    pass
