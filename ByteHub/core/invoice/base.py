from abc import ABC, abstractmethod


class IInvoiceProvider(ABC):
    """Interface for invoice generation providers."""

    @abstractmethod
    def generate(self, order) -> bytes:
        """Generate an invoice for the given order and return its bytes."""
        ...
