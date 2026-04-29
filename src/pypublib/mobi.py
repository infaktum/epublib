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
from collections import namedtuple
from typing import Any

from .book import Book

# ---------------------------------------- Logger ------------------------------------------------

LOGGER = logging.getLogger(__name__)

# -------------------------------------- Mobi Header -----------------------------------------

MobiHeader = namedtuple(typename="MobiHeader",
                        field_names=["uid", "encoding", "compression", "header_length", "has_exth"])


# ------------------------------ MOBI Reading and Creation -----------------

def read_book(file_path: str) -> Book | None:
    """
    Read a Mobi file and return a Book instance.

    Validates the file path and Mobi structure before parsing. Returns None if
    the file cannot be read or parsed.

    Args:
        file_path (str): Path to the Mobi file to read.

    Returns:
        Book | None: A Book instance if successful, None if an error occurs.

    Raises:
        Catches and logs the following exceptions:
            - FileNotFoundError: File does not exist
            - zipfile.BadZipFile: Invalid EPUB container
            - UnicodeDecodeError: Encoding errors in EPUB content
            - KeyError: Missing required EPUB data
            - PermissionError: File permission issues

    Example:
        >>> book = read_book("my_book.mobi")
        >>> if book:
        ...     print(f"Loaded: {book.title}")
    """
    with open(file_path, "rb") as f:
        data = f.read()

        mobi_header, records = parse_mobi_data(data)

        text = get_text(records)
        html = extract_html(records, mobi_header)
        # LOGGER.info(f'Html: {html}')
    return None


def parse_mobi_data(data: bytes) -> tuple[list[Any], MobiHeader]:
    name, num_records = _parse_pdb_header(data)
    records = _parse_records(data, num_records)
    mobi_start, mobi_header = _parse_mobi_header(records)
    LOGGER.info(f'MOBI Header: {mobi_header}')
    parse_exth(mobi_header, mobi_start, records[0])
    return mobi_header, records


# ---------------------------------------- PDB Header -------------------------------------------

def _parse_pdb_header(data):
    header = data[:78]

    name = header[:32].rstrip(b"\x00").decode("utf-8", errors="ignore")
    num_records = struct.unpack(">H", header[76:78])[0]

    LOGGER.info(f'Header: {name}, {num_records} records')

    return name, num_records


# ---------------------------------- Record Table ---------------------------------------------

def _parse_records(data, num_records):
    offset = 78
    record_offsets = []

    for i in range(num_records):
        rec = data[offset:offset + 8]
        rec_offset = struct.unpack(">I", rec[:4])[0]
        record_offsets.append(rec_offset)
        offset += 8
    records = []
    # Record-Daten extrahieren
    for i in range(len(record_offsets)):
        start = record_offsets[i]
        end = record_offsets[i + 1] if i + 1 < len(record_offsets) else len(data)
        records.append(data[start:end])

    return records


# ------------------------------------ MOBI Header---------------------------------------------


def _parse_mobi_header(records):
    record0 = records[0]

    # PalmDOC Header (erste 16 Bytes)
    compression = struct.unpack(">H", record0[0:2])[0]

    # MOBI Header start at offset 16
    mobi_start = 16

    if record0[mobi_start:mobi_start + 4] != b"MOBI":
        raise ValueError("No valid MOBI header found")

    header_length = struct.unpack(">I", record0[mobi_start + 4:mobi_start + 8])[0]
    print(header_length)

    # EXTH-Flag prüfen
    exth_flag = struct.unpack(">I", record0[mobi_start + 128:mobi_start + 132])[0]
    has_exth = exth_flag & 0x40 != 0
    mobi_header = MobiHeader(
        compression=compression, header_length=header_length,
        encoding=struct.unpack(">H", record0[mobi_start + 20:mobi_start + 22])[0],
        uid=struct.unpack(">I", record0[mobi_start + 32:mobi_start + 36])[0],
        has_exth=has_exth
    )

    return mobi_start, mobi_header


# ----------------------------------------------- EXTH (Metadaten)--------------------------------


def parse_exth(mobi_header, mobi_start, record0):
    if not mobi_header.has_exth:
        return

    offset = mobi_start + mobi_header.header_length + 16

    if record0[offset:offset + 4] != b"EXTH":
        return

    length = struct.unpack(">I", record0[offset + 4:offset + 8])[0]
    count = struct.unpack(">I", record0[offset + 8:offset + 12])[0]

    pos = offset + 12

    for _ in range(count):
        record_type = struct.unpack(">I", record0[pos:pos + 4])[0]
        record_len = struct.unpack(">I", record0[pos + 4:pos + 8])[0]
        value = record0[pos + 8:pos + record_len]

        mobi_header.has_exth.setdefault(record_type, []).append(value)

        pos += record_len


# ----------------------------- Text extrahieren (sehr simpel!)-------------------------------------------------

def get_text(records):
    text_data = b"".join(records[1:])  # ab Record 1 = Text
    try:
        return text_data.decode("utf-8", errors="ignore")
    except:
        return text_data.decode("cp1252", errors="ignore")


def extract_html(records, mobi_header):
    """Extrahiert den HTML-Teil aus den Text-Records eines MOBI (Best-Effort)."""
    if not records:
        raise ValueError("No records loaded. Call read() first.")

    text_data = b"".join(records[1:])

    # Dekodierung: erst Header-Encoding, dann robuste Fallbacks
    encodings_to_try = [_get_declared_encoding(mobi_header), "utf-8", "cp1252", "latin-1"]
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


def _get_declared_encoding(mobi_header):
    # https://wiki.mobileread.com/wiki/MOBI
    encoding_map = {
        65001: "utf-8",
        1252: "cp1252",
    }
    encoding = encoding_map.get(mobi_header.encoding)
    LOGGER.debug(f"Encoding:  {mobi_header.encoding}, mapped to {encoding}")
    return encoding
