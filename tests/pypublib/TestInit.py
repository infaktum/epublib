import importlib
import logging
from io import StringIO
import unittest

import pypublib


class TestPackageInit(unittest.TestCase):
    def setUp(self):
        self.pkg = importlib.reload(pypublib)
        self.pkg.logger.handlers.clear()
        self.pkg.logger.addHandler(logging.NullHandler())
        self.pkg.logger.propagate = True

    def test_package_exports_are_available(self):
        self.assertIsNotNone(self.pkg.epub)
        self.assertIsNotNone(self.pkg.book)
        self.assertIsNotNone(self.pkg.markdown)
        self.assertTrue(hasattr(self.pkg, "Book"))
        self.assertTrue(hasattr(self.pkg, "Chapter"))
        self.assertTrue(hasattr(self.pkg, "Html"))

    def test_logger_is_available_without_init(self):
        self.assertFalse(self.pkg.is_initialized())
        self.assertIsNotNone(self.pkg.logger)
        self.assertEqual(self.pkg.logger.name, "pypublib")
        self.assertTrue(any(isinstance(handler, logging.NullHandler) for handler in self.pkg.logger.handlers))

    def test_get_logger_uses_package_namespace(self):
        epub_logger = self.pkg.get_logger("epub")
        self.assertEqual(epub_logger.name, "pypublib.epub")
        self.assertIs(self.pkg.get_logger("pypublib.epub"), epub_logger)

    def test_init_marks_initialized_and_sets_log_level(self):
        config = self.pkg.init({"theme": "dark"}, log_level=logging.INFO)

        self.assertTrue(self.pkg.is_initialized())
        self.assertEqual(config["theme"], "dark")
        self.assertEqual(config["log_level"], logging.INFO)
        self.assertEqual(self.pkg.logger.level, logging.INFO)

    def test_configure_logging_replaces_null_handler_with_stream_handler(self):
        stream = StringIO()

        logger = self.pkg.configure_logging(logging.INFO, stream=stream, force=True)
        logger.info("hello world")

        self.assertEqual(logger.level, logging.INFO)
        self.assertTrue(any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers))
        self.assertIn("hello world", stream.getvalue())


if __name__ == "__main__":
    unittest.main()

