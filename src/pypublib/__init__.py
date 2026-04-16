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

# Use relative imports so the local package is resolved correctly when the
# project lives in a `src/` layout and tests insert `src` into sys.path.
from . import epub as epub  # noqa: F401
from .epub import read_book, publish_book  # noqa: F401
from . import book as book  # noqa: F401
from .book import Book, Chapter  # noqa: F401
from . import markdown as markdown  # noqa: F401
from .markdown import Html  # noqa: F401

# Public names exported by the package
__all__ = [
	"__version__",
	"__author__",
	"epub",
	"read_book",
	"publish_book",
	"book",
	"Book",
	"Chapter",
	"markdown",
	"Html",
]
