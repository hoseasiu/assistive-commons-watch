from abc import ABC, abstractmethod

from .models import Source


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> Source:
        """Fetch live platform data for the given source URL."""
        ...


class SourceNotFoundError(ValueError):
    """The upstream project no longer exists (or is private) - a permanent condition, not a transient failure."""
