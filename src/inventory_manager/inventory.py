"""The Inventory class: owns the products, the sales and all the business rules."""

from __future__ import annotations

from collections import defaultdict  # a dict that creates missing keys automatically
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterator  # Iterator[Sale] = "something you can loop over that yields Sales"

from .exceptions import DuplicateProductError, OutOfStockError, ProductNotFoundError  # the dot = "from this package"
from .logging_utils import log_change
from .models import Product, Sale


class Inventory:
    """A shop's stock and sales history."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}  # key = lowercase name, value = Product
        self._sales: list[Sale] = []  # every sale, oldest first
        # The leading _ means "private": change these only through the methods below.

    @staticmethod  # doesn't need self; it's just a helper that lives in the class
    def _key(name: str) -> str:
        return name.strip().lower()  # "  Sugar " and "sugar" become the same key "sugar"

    # ---------- changing things (each one is logged by @log_change) ----------

    @log_change  # wrap this method with our logging decorator
    def add_product(
        self, name: str, unit_price: Decimal | str, quantity: int, low_stock_threshold: int = 5
    ) -> Product:
        key = self._key(name)
        if key in self._products:  # rule: no two products with the same name
            raise DuplicateProductError(name)
        product = Product(name, Decimal(str(unit_price)), quantity, low_stock_threshold)  # validates itself
        self._products[key] = product  # store it
        return product

    @log_change
    def restock(self, name: str, quantity: int) -> Product:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive.")
        product = self.get_product(name)  # raises ProductNotFoundError if missing
        product.quantity += quantity  # same as: product.quantity = product.quantity + quantity
        return product

    @log_change
    def record_sale(self, name: str, quantity: int, when: datetime | None = None) -> Sale:
        if quantity <= 0:
            raise ValueError("Sale quantity must be positive.")
        product = self.get_product(name)
        if quantity > product.quantity:  # THE key rule: refuse if there isn't enough stock
            raise OutOfStockError(product.name, quantity, product.quantity)
        product.quantity -= quantity  # lower the stock
        sale = Sale(
            product_name=product.name,
            quantity=quantity,
            unit_price=product.unit_price,
            timestamp=when or datetime.now(),  # use `when` if given, otherwise right now
        )
        self._sales.append(sale)  # add to the history
        return sale

    # ---------- reading things ----------

    def get_product(self, name: str) -> Product:
        try:
            return self._products[self._key(name)]
        except KeyError:  # a dict raises KeyError when the key is missing
            raise ProductNotFoundError(name) from None  # replace it with our clearer error

    def list_products(self) -> list[Product]:
        return sorted(self._products.values(), key=lambda p: p.name.lower())  # alphabetical order

    def low_stock(self) -> list[Product]:
        return [p for p in self.list_products() if p.is_low_stock]  # list comprehension = filter

    def iter_sales(self, start: date | None = None, end: date | None = None) -> Iterator[Sale]:
        """Generator: hands out sales one at a time instead of building a list."""
        for sale in self._sales:
            day = sale.timestamp.date()  # just the date part of the timestamp
            if start is not None and day < start:  # skip sales before `start`
                continue
            if end is not None and day > end:  # skip sales after `end`
                continue
            yield sale  # pause here, hand back one sale, resume on the next loop step

    def daily_sales_totals(self) -> dict[date, Decimal]:
        totals: defaultdict[date, Decimal] = defaultdict(Decimal)  # a missing day starts at Decimal(0)
        for sale in self.iter_sales():  # uses our generator
            totals[sale.timestamp.date()] += sale.total  # add this sale's money to its day
        return dict(sorted(totals.items()))  # a normal dict, sorted by date

    # ---------- converting to/from plain data (for JSON) ----------

    def to_dict(self) -> dict[str, Any]:
        return {
            "products": [p.to_dict() for p in self.list_products()],
            "sales": [s.to_dict() for s in self._sales],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Inventory:
        inventory = cls()  # start with an empty Inventory
        for item in data.get("products", []):
            product = Product.from_dict(item)
            inventory._products[cls._key(product.name)] = product  # direct insert: avoids logging a "change" on load
        inventory._sales = [Sale.from_dict(s) for s in data.get("sales", [])]
        return inventory