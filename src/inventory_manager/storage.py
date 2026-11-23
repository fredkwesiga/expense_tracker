"""Saving and loading the inventory as a JSON file."""

from __future__ import annotations

import json  # converts between Python dicts/lists and JSON text
from pathlib import Path

from .exceptions import StorageError
from .inventory import Inventory


def save_inventory(inventory: Inventory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)  # create the folder if it doesn't exist
    tmp = path.with_suffix(".tmp")  # e.g. inventory.tmp next to inventory.json
    with tmp.open("w", encoding="utf-8") as f:  # `with` closes the file automatically
        json.dump(inventory.to_dict(), f, indent=2)  # write the dict as pretty JSON
    tmp.replace(path)  # swap in the new file in one step: a crash mid-write can't corrupt your data


def load_inventory(path: Path) -> Inventory:
    if not path.exists():  # first run: no file yet
        return Inventory()  # so start empty
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)  # read JSON text into a dict
        return Inventory.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:  # broken or wrong-shaped file
        raise StorageError(f"Could not read {path}: {exc}") from exc