"""The @log_change decorator: writes a line to a log file for every change."""

from __future__ import annotations

import functools  # gives us functools.wraps
import logging  # Python's built-in logging system
from pathlib import Path  # a nicer way to handle file paths than plain strings
from typing import Callable, ParamSpec, TypeVar  # tools for type-hinting decorators

P = ParamSpec("P")  # stands for "whatever parameters the decorated function takes"
R = TypeVar("R")  # stands for "whatever the decorated function returns"

change_logger = logging.getLogger("inventory_manager.changes")  # a named logger for our app


def configure_change_log(path: str | Path) -> None:
    """Send log lines to a file. Call this once when the program starts."""
    handler = logging.FileHandler(path, encoding="utf-8")  # a handler decides WHERE lines go
    handler.setFormatter(  # a formatter decides what each line LOOKS like
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")  # time | level | text
    )
    change_logger.addHandler(handler)  # attach the file handler to our logger
    change_logger.setLevel(logging.INFO)  # record INFO and anything more serious
    change_logger.propagate = False  # don't also print these lines in the terminal


def log_change(func: Callable[P, R]) -> Callable[P, R]:  # takes a function, returns a function
    """Decorator: wraps a method so every call to it gets logged."""

    @functools.wraps(func)  # copies func's name and docstring onto wrapper
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:  # accepts any arguments at all
        shown = [repr(a) for a in args[1:]]  # args[0] is self, so skip it; repr adds quotes to strings
        shown += [f"{k}={v!r}" for k, v in kwargs.items()]  # keyword args shown as key=value
        call = f"{func.__name__}({', '.join(shown)})"  # e.g. "record_sale('Sugar', 2)"
        try:
            result = func(*args, **kwargs)  # run the REAL method
        except Exception as exc:  # if it failed...
            change_logger.warning("FAILED %s -> %s: %s", call, type(exc).__name__, exc)  # log the failure
            raise  # ...then re-raise the same error so the caller still sees it
        change_logger.info("%s -> %r", call, result)  # log the success and what it returned
        return result  # hand the result back as if nothing happened

    return wrapper  # the decorated method is now this wrapper