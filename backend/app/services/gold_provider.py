from abc import ABC, abstractmethod


class GoldProvider(ABC):
    @abstractmethod
    def latest(self) -> dict:
        """Return normalized latest XAU price data."""
