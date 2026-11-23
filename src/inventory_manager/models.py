"""Data objects: Product and Sale. They hold data and validate it, nothing more."""

from __future__ import annotations  # allows "-> Product" inside the Product class itself

from dataclasses import dataclass  # @dataclass writes __init__, __repr__, __eq__ for us
from datetime import datetime  # a date + time, used to timestamp sales
from decimal import Decimal, InvalidOperation  # exact decimal numbers for money
from typing import Any  # "any type", used for values loaded from JSON


def to_money(value: Decimal | int | float | str) -> Decimal:  # accepts several input types
    """Convert a value to a Decimal rounded to 2 decimal places."""
    try:  # try the conversion; it may fail for input like "abc"
        return Decimal(str(value)).quantize(Decimal("0.01"))  # str() first avoids float errors
    except InvalidOperation as exc:  # Decimal("abc") raises InvalidOperation
        raise ValueError(f"'{value}' is not a valid amount.") from exc  # turn it into a clearer error


@dataclass  # generates __init__(self, name, unit_price, quantity, low_stock_threshold=5)
class Product:
    """A product on the shop's shelves."""

    name: str  # field 1: product name
    unit_price: Decimal  # field 2: price of one unit
    quantity: int  # field 3: units in stock
    low_stock_threshold: int = 5  # field 4 with a default: "low" when stock <= this

    def __post_init__(self) -> None:  # dataclass calls this right after __init__
        self.name = self.name.strip()  # remove spaces at the start/end: "  Sugar " -> "Sugar"
        self.unit_price = to_money(self.unit_price)  # make sure the price is a clean Decimal
        if not self.name:  # an empty string counts as False
            raise ValueError("Product name cannot be empty.")
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if self.low_stock_threshold < 0:
            raise ValueError("Low-stock threshold cannot be negative.")

    @property  # lets you write product.is_low_stock (no brackets), like an attribute
    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold  # True or False

    def to_dict(self) -> dict[str, Any]:  # turn the object into a plain dict that JSON can save
        return {
            "name": self.name,
            "unit_price": str(self.unit_price),  # JSON has no Decimal, so save it as text "4500.00"
            "quantity": self.quantity,
            "low_stock_threshold": self.low_stock_threshold,
        }

    @classmethod  # called on the class itself: Product.from_dict(data); cls means Product
    def from_dict(cls, data: dict[str, Any]) -> Product:  # rebuild a Product from a dict
        return cls(
            name=data["name"],
            unit_price=Decimal(data["unit_price"]),  # text "4500.00" back to Decimal
            quantity=int(data["quantity"]),
            low_stock_threshold=int(data.get("low_stock_threshold", 5)),  # .get gives 5 if the key is missing
        )


@dataclass(frozen=True)  # frozen = cannot be changed after creation (sale history is permanent)
class Sale:
    """One completed sale."""

    product_name: str  # what was sold
    quantity: int  # how many units
    unit_price: Decimal  # price AT THE TIME of sale (later price changes don't rewrite history)
    timestamp: datetime  # when it happened

    @property
    def total(self) -> Decimal:  # money earned from this sale
        return self.unit_price * self.quantity

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
            "timestamp": self.timestamp.isoformat(timespec="seconds"),  # e.g. "2026-11-23T10:30:00"
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Sale:
        return cls(
            product_name=data["product_name"],
            quantity=int(data["quantity"]),
            unit_price=Decimal(data["unit_price"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),  # text back to datetime
        )