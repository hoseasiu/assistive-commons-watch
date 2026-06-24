from abc import ABC, abstractmethod

from .models import Source


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> Source:
        """Fetch live platform data for the given source URL."""
        ...
