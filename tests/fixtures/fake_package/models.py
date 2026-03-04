"""Model classes with various patterns."""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration object.

    Args:
        host: Server hostname.
        port: Server port number.
        debug: Enable debug mode.
    """

    host: str = "localhost"
    port: int = 8080
    debug: bool = False

    def validate(self) -> bool:
        """Check if config is valid."""
        return bool(self.host) and 0 < self.port < 65536


class Connection:
    """A stateful connection object."""

    def __init__(self, config: Config):
        """Initialize connection.

        Args:
            config: Connection configuration.
        """
        self.config = config
        self._connected = False

    def connect(self) -> None:
        """Establish the connection."""
        self._connected = True

    def disconnect(self) -> None:
        """Close the connection."""
        self._connected = False

    def execute(self, query: str, params: dict | None = None) -> list:
        """Execute a query.

        Args:
            query: The query string.
            params: Optional query parameters.

        Returns:
            Query results.
        """
        return []
