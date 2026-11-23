from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from inventory_manager.exceptions import DuplicateProductError, OutOfStockError, ProductNotFoundError
from inventory_manager.inventory import Inventory
from inventory_manager.storage import load_inventory, save_inventory


@pytest.fixture  # a fixture = reusable setup; any test that takes `inv` as a parameter gets this
def inv() -> Inventory:
    inventory = Inventory()
    inventory.add_product("Sugar", Decimal("4500"), 10)
    inventory.add_product("Salt", Decimal("1000"), 3)
    return inventory


def test_sale_lowers_stock(inv: Inventory) -> None:
    inv.record_sale("Sugar", 4)
    assert inv.get_product("sugar").quantity == 6  # assert = "this must be true, or the test fails"


def test_oversell_is_refused(inv: Inventory) -> None:
    with pytest.raises(OutOfStockError):  # the test passes only if this error is raised
        inv.record_sale("Salt", 5)
    assert inv.get_product("Salt").quantity == 3  # stock untouched


def test_duplicate_and_missing(inv: Inventory) -> None:
    with pytest.raises(DuplicateProductError):
        inv.add_product("SUGAR", Decimal("1"), 1)
    with pytest.raises(ProductNotFoundError):
        inv.record_sale("Rice", 1)


def test_low_stock(inv: Inventory) -> None:
    assert [p.name for p in inv.low_stock()] == ["Salt"]


def test_daily_totals(inv: Inventory) -> None:
    inv.record_sale("Sugar", 2, when=datetime(2026, 11, 22, 9))
    inv.record_sale("Salt", 1, when=datetime(2026, 11, 22, 15))
    inv.record_sale("Sugar", 1, when=datetime(2026, 11, 23, 10))
    assert inv.daily_sales_totals() == {
        date(2026, 11, 22): Decimal("10000.00"),
        date(2026, 11, 23): Decimal("4500.00"),
    }


def test_save_and_load(inv: Inventory, tmp_path: Path) -> None:  # tmp_path = a throwaway folder from pytest
    inv.record_sale("Sugar", 1)
    file = tmp_path / "data.json"
    save_inventory(inv, file)
    loaded = load_inventory(file)
    assert loaded.to_dict() == inv.to_dict()