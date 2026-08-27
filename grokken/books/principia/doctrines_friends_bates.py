"""
Handler for "The Doctrines of Friends, or, Principles of the Christian Religion"
by Elisha Bates (1825).

A work on Quaker theology and principles. The oldest book in the Principia 34.

Score: 38.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "THE ORIGINAL AND PRESENT",
        "STATE OF MAN.",
        "THE UNIVERSALITY OF GRACE.",
        "THE DIVINITY OF JESUS CHRIST.",
        "THE SCRIPTURES.",
        "OF IMMEDIATE REVELATION.",
        "THE MINISTRY.",
        "OF BAPTISM.",
        "OF WORSHIP.",
        "THE SUPPER.",
        "OF DAYS AND TIMES.",
        "OF SALUTATIONS AND RECREATIONS.",
        "OF OATHS.",
        "OF WAR.",
        "OF REWARDS AND PUNISHMENTS.",
        "OF PERFECTION AND PERSEVERANCE.",
        "OF SANCTIFICATION AND JUSTIFICATION.",
        "THE CONCLUSION.",
    }
)

_SCAN_GARBAGE_LINES = frozenset({"с", "Ꭰ", "解", "善", "་ ་ ་", "ܢ", "Ꮓ", "蜀", "删", "နတ်"})


def _remove_page_furniture(text: str) -> str:
    """Remove this edition's exact running labels beside page numbers."""
    lines = text.splitlines()
    clear: set[int] = {
        index for index, line in enumerate(lines) if line.strip() in _SCAN_GARBAGE_LINES
    }
    for index, line in enumerate(lines):
        if not re.fullmatch(r"[ \t]*\d{1,4}[ \t]*", line):
            continue
        found_header = False
        for step in (-1, 1):
            cursor = index + step
            while 0 <= cursor < len(lines):
                if not lines[cursor].strip():
                    cursor += step
                    continue
                if lines[cursor].strip() not in _RUNNING_HEADERS:
                    break
                clear.add(cursor)
                found_header = True
                cursor += step
        if found_header:
            clear.add(index)
    return "\n".join(line for index, line in enumerate(lines) if index not in clear)


class DoctrinesOfFriends(BookProcessor):
    """
    Processor for The Doctrines of Friends.
    """

    barcode = "HWJN82"
    title = "The Doctrines of Friends, or, Principles of the Christian Religion"
    author = "Bates, Elisha"
    date = "1825"

    notes = """
    Quaker theological work, oldest book in the collection (1825).

    Known quirks:
    - Older typography and spelling conventions
    - Religious/theological content
    - Biblical references and quotations
    - May have more OCR issues due to age of source material
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1825 text
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Doctrines of Friends."""
        text = _remove_page_furniture(text)

        # Everything after the explicit terminator is a pasted library due slip.
        end = text.find("\nTHE END.")
        if end >= 0:
            text = text[: end + len("\nTHE END.")]

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
