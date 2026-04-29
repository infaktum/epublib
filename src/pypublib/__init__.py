"""
Top-level package for pypublib.

A Python library for creating and manipulating EPUB electronic publications.

This module exposes commonly used classes and functions so users can import them
as follows:

    - ``from pypublib import Book`` - Import the Book class
    - ``from pypublib import Chapter`` - Import the Chapter class
    - ``from pypublib import read_book, publish_book`` - Import EPUB I/O functions
    - ``from pypublib import Html`` - Import HTML generation utilities
    - ``from pypublib import markdown`` - Import Markdown conversion module

Attributes:
    __version__ (str): Current version of pypublib.
    __author__ (str): Primary author of pypublib.
"""

__version__ = "0.1.1"
__author__ = "Heiko Sippel"

import logging
from typing import Optional, Dict, Any

# ------------------------------- Logging ---------------------------------------


logger = logging.getLogger("pypublib")
_pypublib_logger = logger
_initialized: bool = False
_config: Dict[str, Any] = {}

if not _pypublib_logger.handlers:
    _pypublib_logger.addHandler(logging.NullHandler())


def get_logger(name: str):
    if isinstance(name, str) and name.startswith("pypublib"):
        return logging.getLogger(name)
    return logging.getLogger(f"pypublib.{name}")


def configure_logging(
    log_level: int = logging.INFO,
    *,
    stream=None,
    formatter: Optional[logging.Formatter] = None,
    force: bool = False,
) -> logging.Logger:
    """Configure the package logger with a console handler when needed.

    If only the default ``NullHandler`` is present, it is replaced by a
    ``StreamHandler`` so ``LOGGER.info(...)`` becomes visible without requiring
    the application to configure logging first.
    """
    pkg_logger = _pypublib_logger
    pkg_logger.setLevel(log_level)

    has_real_handler = any(not isinstance(handler, logging.NullHandler) for handler in pkg_logger.handlers)
    if force:
        has_real_handler = False

    if not has_real_handler:
        for handler in list(pkg_logger.handlers):
            pkg_logger.removeHandler(handler)

        handler = logging.StreamHandler(stream)
        handler.setLevel(log_level)
        handler.setFormatter(formatter or logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False

    return pkg_logger


# -------------------------------- Imports ---------------------------------

from . import epub as epub
from .epub import read_book, publish_book
from . import book as book
from .book import Book, Chapter
from . import markdown as markdown
from .markdown import Html

# Public names exported by the package
__all__ = [
    "__version__",
    "__author__",
    "logger",
    "get_logger",
    "configure_logging",
    "init",
    "is_initialized",
    "epub",
    "read_book",
    "publish_book",
    "book",
    "Book",
    "Chapter",
    "markdown",
    "Html",
]

# -------------------------------- Initialization -------------------------------


_initialized: bool = False
_config: Dict[str, Any] = {}


def init(settings: Optional[Dict[str, Any]] = None, *, log_level: Optional[int] = None) -> Dict[str, Any]:
    global _initialized, _config

    if settings is None:
        settings = {}

    cfg = {**settings}

    if log_level is not None:
        configure_logging(log_level)
        cfg["log_level"] = log_level

    _config = cfg
    _initialized = True
    logging.getLogger(__name__).debug("pypublib initialized: %s", _config)
    return _config


def is_initialized() -> bool:
    return _initialized
