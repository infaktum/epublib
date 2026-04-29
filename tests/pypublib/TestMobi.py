#  MIT License
#  #
#  Copyright (c) 2026 Heiko Sippel
#  #
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  #
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#  #
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

import unittest

from pypublib.mobi import MobiParser


class TestMobiParser(unittest.TestCase):
    def test_extract_html_requires_loaded_records(self):
        parser = MobiParser("dummy.mobi")
        with self.assertRaises(ValueError):
            parser.extract_html()

    def test_extract_html_returns_html_block(self):
        parser = MobiParser("dummy.mobi")
        parser.mobi_header = {"encoding": 65001}
        parser.records = [
            b"header",
            b"junk\x00\x00<html><head><title>T</title></head><body><p>Hello</p></body></html>tail",
        ]

        html = parser.extract_html()

        self.assertTrue(html.lower().startswith("<html"))
        self.assertTrue(html.lower().endswith("</html>"))
        self.assertIn("<p>Hello</p>", html)

    def test_extract_html_falls_back_to_body(self):
        parser = MobiParser("dummy.mobi")
        parser.mobi_header = {"encoding": 65001}
        parser.records = [b"header", b"prefix<body><p>X</p></body>suffix"]

        html = parser.extract_html()

        self.assertTrue(html.lower().startswith("<body"))
        self.assertTrue(html.lower().endswith("</body>"))

    def test_extract_html_returns_clean_text_if_no_tags(self):
        parser = MobiParser("dummy.mobi")
        parser.mobi_header = {"encoding": 65001}
        parser.records = [b"header", b"abc\x00def"]

        html = parser.extract_html()

        self.assertEqual(html, "abcdef")


if __name__ == "__main__":
    unittest.main()
