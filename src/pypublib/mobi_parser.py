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
import logging
import struct
import re

# ---------------------------------------- Logger ------------------------------------------------

LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------------------
class MobiParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.records = []
        self.mobi_header = {}
        self.exth = {}

    def read(self):
        with open(self.filepath, "rb") as f:
            self.data = f.read()

        self._parse_pdb_header()
        self._parse_records()
        self._parse_mobi_header()
        self._parse_exth()

    # --------------------------------------------------
    # 1. PDB Header
    # --------------------------------------------------
    def _parse_pdb_header(self):
        header = self.data[:78]

        self.name = header[:32].rstrip(b"\x00").decode("utf-8", errors="ignore")
        self.num_records = struct.unpack(">H", header[76:78])[0]

    # --------------------------------------------------
    # 2. Record Table
    # --------------------------------------------------
    def _parse_records(self):
        offset = 78
        self.record_offsets = []

        for i in range(self.num_records):
            rec = self.data[offset:offset + 8]
            rec_offset = struct.unpack(">I", rec[:4])[0]
            self.record_offsets.append(rec_offset)
            offset += 8

        # Record-Daten extrahieren
        for i in range(len(self.record_offsets)):
            start = self.record_offsets[i]
            end = self.record_offsets[i + 1] if i + 1 < len(self.record_offsets) else len(self.data)
            self.records.append(self.data[start:end])

    # --------------------------------------------------
    # 3. MOBI Header
    # --------------------------------------------------
    def _parse_mobi_header(self):
        record0 = self.records[0]

        # PalmDOC Header (erste 16 Bytes)
        compression = struct.unpack(">H", record0[0:2])[0]

        # MOBI Header beginnt typischerweise bei Offset 16
        mobi_start = 16

        if record0[mobi_start:mobi_start + 4] != b"MOBI":
            raise ValueError("No valid MOBI header found")

        header_length = struct.unpack(">I", record0[mobi_start + 4:mobi_start + 8])[0]

        self.mobi_header = {
            "compression": compression,
            "header_length": header_length,
            "encoding": struct.unpack(">I", record0[mobi_start + 28:mobi_start + 32])[0],
            "uid": struct.unpack(">I", record0[mobi_start + 32:mobi_start + 36])[0],
        }

        # EXTH-Flag prüfen
        exth_flag = struct.unpack(">I", record0[mobi_start + 128:mobi_start + 132])[0]
        self.has_exth = exth_flag & 0x40 != 0

        self.mobi_header["has_exth"] = self.has_exth
        self.mobi_start = mobi_start
        self.record0 = record0

    # --------------------------------------------------
    # 4. EXTH (Metadaten)
    # --------------------------------------------------
    def _parse_exth(self):
        if not self.has_exth:
            return

        offset = self.mobi_start + self.mobi_header["header_length"] + 16

        if self.record0[offset:offset + 4] != b"EXTH":
            return

        length = struct.unpack(">I", self.record0[offset + 4:offset + 8])[0]
        count = struct.unpack(">I", self.record0[offset + 8:offset + 12])[0]

        pos = offset + 12

        for _ in range(count):
            record_type = struct.unpack(">I", self.record0[pos:pos + 4])[0]
            record_len = struct.unpack(">I", self.record0[pos + 4:pos + 8])[0]
            value = self.record0[pos + 8:pos + record_len]

            self.exth.setdefault(record_type, []).append(value)

            pos += record_len

    # --------------------------------------------------
    # 5. Text extrahieren (sehr simpel!)
    # --------------------------------------------------
    def get_text(self):
        text_data = b"".join(self.records[1:])  # ab Record 1 = Text
        try:
            return text_data.decode("utf-8", errors="ignore")
        except:
            return text_data.decode("cp1252", errors="ignore")

    def _get_declared_encoding(self):
        """Mappt bekannte MOBI-Encoding-IDs auf Python-Encodingnamen."""
        # https://wiki.mobileread.com/wiki/MOBI
        encoding_map = {
            65001: "utf-8",
            1252: "cp1252",
        }
        return encoding_map.get(self.mobi_header.get("encoding"))

    def extract_html(self):
        """Extrahiert den HTML-Teil aus den Text-Records eines MOBI (Best-Effort)."""
        if not self.records:
            raise ValueError("No records loaded. Call read() first.")

        text_data = b"".join(self.records[1:])

        # Dekodierung: erst Header-Encoding, dann robuste Fallbacks
        encodings_to_try = [self._get_declared_encoding(), "utf-8", "cp1252", "latin-1"]
        decoded = ""
        for enc in [e for e in encodings_to_try if e]:
            try:
                decoded = text_data.decode(enc, errors="ignore")
                break
            except Exception:
                continue

        if not decoded:
            return ""

        cleaned = decoded.replace("\x00", "")

        # Start-Tag bevorzugt auf <html>, dann <body>
        start_match = re.search(r"<html\b", cleaned, flags=re.IGNORECASE)
        if not start_match:
            start_match = re.search(r"<body\b", cleaned, flags=re.IGNORECASE)

        if not start_match:
            return cleaned.strip()

        start_idx = start_match.start()

        # Ende bevorzugt auf </html>, dann </body>
        end_match = None
        for pattern in (r"</html>", r"</body>"):
            matches = list(re.finditer(pattern, cleaned, flags=re.IGNORECASE))
            if matches:
                end_match = matches[-1]
                break

        if end_match:
            end_idx = end_match.end()
            return cleaned[start_idx:end_idx].strip()

        return cleaned[start_idx:].strip()
