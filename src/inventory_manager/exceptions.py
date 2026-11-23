"""Custom exceptions for the inventory manager."""  # a docstring: describes the module

from __future__ import annotations  # lets type hints refer to classes not yet defined


class InventoryError(Exception):  # our base error; it inherits from Python's built-in Exception
    """Base class for every error raised by this package."""


class ProductNotFoundError(InventoryError):  # a more specific error; it IS an InventoryError
    """Raised when a product name does not exist."""

    def __init__(self, name: str) -> None:  # runs when we do: raise ProductNotFoundError("Sugar")
        super().__init__(f"No product called '{name}'.")  # passes the message up to Exception
        self.name = name  # keep the name on the error so code catching it can read it


class DuplicateProductError(InventoryError):
    """Raised when adding a product whose name is already taken."""

    def __init__(self, name: str) -> None:
        super().__init__(f"A product called '{name}' already exists.")
        self.name = name


class OutOfStockError(InventoryError):
    """Raised when a sale asks for more units than are in stock."""

    def __init__(self, name: str, requested: int, available: int) -> None:
        super().__init__(
            f"Cannot sell {requested} x '{name}': only {available} in stock."
        )
        self.name = name  # which product
        self.requested = requested  # how many the customer wanted
        self.available = available  # how many we actually had


class StorageError(InventoryError):
    """Raised when the JSON data file cannot be read or is corrupt."""