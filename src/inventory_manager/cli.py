"""The terminal menu. It only asks questions and prints answers; the rules live in Inventory."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from .exceptions import InventoryError
from .inventory import Inventory
from .logging_utils import configure_change_log
from .storage import load_inventory, save_inventory

DATA_FILE = Path("inventory.json")  # saved in whatever folder you run the program from
LOG_FILE = Path("changes.log")


def ask_text(prompt: str) -> str:
    while True:  # keep asking until we get something
        answer = input(prompt).strip()
        if answer:
            return answer
        print("Please type something.")


def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))  # int("abc") raises ValueError
        except ValueError:
            print("Please enter a whole number.")


def ask_price(prompt: str) -> Decimal:
    while True:
        try:
            return Decimal(input(prompt).strip())
        except InvalidOperation:  # Decimal("abc") raises InvalidOperation
            print("Please enter a number, e.g. 4500 or 12.50.")


def handle_add(inventory: Inventory) -> None:
    name = ask_text("Product name: ")
    price = ask_price("Unit price: ")
    qty = ask_int("Quantity: ")
    product = inventory.add_product(name, price, qty)
    print(f"Added {product.name}.")


def handle_restock(inventory: Inventory) -> None:
    name = ask_text("Product name: ")
    qty = ask_int("Units to add: ")
    product = inventory.restock(name, qty)
    print(f"{product.name} now has {product.quantity} in stock.")


def handle_sale(inventory: Inventory) -> None:
    name = ask_text("Product name: ")
    qty = ask_int("Quantity sold: ")
    sale = inventory.record_sale(name, qty)
    print(f"Sold {sale.quantity} x {sale.product_name} for {sale.total:,.2f}.")  # :,.2f -> 13,500.00


def handle_list(inventory: Inventory) -> None:
    products = inventory.list_products()
    if not products:
        print("No products yet.")
        return
    print(f"{'Name':<20}{'Price':>12}{'Qty':>6}")  # <20 = left-align in 20 chars, >12 = right-align
    for p in products:
        flag = "  LOW" if p.is_low_stock else ""
        print(f"{p.name:<20}{p.unit_price:>12,.2f}{p.quantity:>6}{flag}")


def handle_low_stock(inventory: Inventory) -> None:
    low = inventory.low_stock()
    if not low:
        print("Nothing is low on stock.")
    for p in low:
        print(f"{p.name}: {p.quantity} left (threshold {p.low_stock_threshold})")


def handle_daily_report(inventory: Inventory) -> None:
    totals = inventory.daily_sales_totals()
    if not totals:
        print("No sales yet.")
    for day, total in totals.items():
        print(f"{day.isoformat()}  {total:>14,.2f}")


def handle_history(inventory: Inventory) -> None:
    for sale in inventory.iter_sales():  # streamed one record at a time by the generator
        print(f"{sale.timestamp:%Y-%m-%d %H:%M}  {sale.quantity} x {sale.product_name}  = {sale.total:,.2f}")


MENU = {  # maps the key the user types -> (label, function to call)
    "1": ("Add product", handle_add),
    "2": ("Restock product", handle_restock),
    "3": ("Record sale", handle_sale),
    "4": ("List products", handle_list),
    "5": ("Low stock", handle_low_stock),
    "6": ("Daily sales report", handle_daily_report),
    "7": ("Sales history", handle_history),
}


def main() -> None:
    configure_change_log(LOG_FILE)  # start logging changes to changes.log
    try:
        inventory = load_inventory(DATA_FILE)
    except InventoryError as exc:
        print(f"Error: {exc}")
        return  # stop: don't overwrite a broken file
    while True:  # the main loop: show the menu until the user quits
        print()
        for key, (label, _) in MENU.items():  # _ means "I don't need this value"
            print(f"{key}) {label}")
        print("0) Quit")
        choice = input("> ").strip()
        if choice == "0":
            print("Goodbye.")
            break  # leave the loop -> program ends
        if choice not in MENU:
            print("Unknown option.")
            continue  # skip back to the top of the loop
        _, action = MENU[choice]
        try:
            action(inventory)  # call the chosen handle_... function
            save_inventory(inventory, DATA_FILE)  # save after every action
        except InventoryError as exc:  # business-rule errors, e.g. OutOfStockError
            print(f"Error: {exc}")
        except ValueError as exc:  # validation errors, e.g. negative quantity
            print(f"Invalid input: {exc}")