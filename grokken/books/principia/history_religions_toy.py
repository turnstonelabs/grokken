"""
Handler for "Introduction to the History of Religions" by Crawford Howell Toy (1913).

A scholarly introduction to comparative religion, part of the Handbooks on
the History of Religions series edited by Morris Jastrow Jr.

Score: 38.8
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "NATURE OF RELIGION",
        "THE SOUL",
        "EARLY RELIGIOUS CEREMONIES",
        "EARLY CULTS",
        "TOTEMISM AND TABOO",
        "GODS",
        "MYTHS",
        "MAGIC AND DIVINATION",
        "SOCIAL DEVELOPMENT OF RELIGION",
        "THE HIGHER THEISTIC DEVELOPMENT",
        "SCIENTIFIC AND ETHICAL ELEMENTS",
        "INDEX",
    }
)

_SCAN_GARBAGE_LINES = frozenset({"عيرة", "ив", "пол", "да", "ვ", "།", "་", "९", "१९", "९९"})


def _remove_page_furniture(text: str) -> str:
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


class HistoryOfReligions(BookProcessor):
    """
    Processor for Introduction to the History of Religions.
    """

    barcode = "TZ1WHG"
    title = "Introduction to the History of Religions"
    author = "Toy, Crawford Howell"
    date = "1913"

    notes = """
    Academic text on comparative religion.

    Known quirks:
    - Library stamps at beginning (Tozzer Library, Peabody Museum)
    - Extensive footnotes with superscript numbers
    - Running headers "INTRODUCTION TO HISTORY OF RELIGIONS"
    - References to other works (Records of the Past, etc.)
    - Section numbers (e.g., "728.")
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Introduction to History of Religions."""
        # Remove running headers with page numbers
        text = re.sub(
            r"^\s*\d+\s+INTRODUCTION TO HISTORY OF RELIGIONS\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*INTRODUCTION TO HISTORY OF RELIGIONS\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = _remove_page_furniture(text)

        # Two page-break splits remain only because folios intervened.
        text = text.replace("Aphro-\n\nditon", "Aphroditon")
        text = text.replace("vic-\n\nof Judas", "victory of Judas")

        # The index is followed by a pasted library due slip.
        due_slip = text.find("\nDATE DUE")
        if due_slip >= 0:
            text = text[:due_slip]

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
