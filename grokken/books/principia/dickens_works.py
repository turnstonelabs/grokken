"""
Handler for "The Works of Charles Dickens" (1911 Anniversary Edition).

Part of a collected works edition with introductions by Andrew Lang,
Frederic G. Kitton, John Forster, G. K. Chesterton, George Gissing, and others.

Score: 38.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "POSTHUMOUS PAPERS OF",
        "THE PICKWICK CLUB.",
        "INTRODUCTION.",
        "CRITICAL COMMENTS.",
    }
)

_SCAN_GARBAGE_LINES = frozenset({"ིའི་", "က", "دو", "در"})


def _remove_page_furniture(text: str) -> str:
    """Remove exact running labels only when attached to a page number."""
    lines = text.splitlines()
    clear: set[int] = set()

    for index, line in enumerate(lines):
        arabic_page = re.fullmatch(r"[ \t]*\d{1,4}[ \t]*", line)
        roman_page = re.fullmatch(r"(?i)[ \t]*[ivxlcdm]{1,12}[ \t]*", line)
        if not (arabic_page or roman_page):
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

    clear.update(index for index, line in enumerate(lines) if line.strip() in _SCAN_GARBAGE_LINES)
    return "\n".join(line for index, line in enumerate(lines) if index not in clear)


class DickensWorks(BookProcessor):
    """
    Processor for The Works of Charles Dickens.
    """

    barcode = "HWABNK"
    title = "The Works of Charles Dickens"
    author = "Dickens, Charles"
    date = "1911"

    notes = """
    Anniversary Edition of Dickens's collected works, specifically Pickwick Papers Part I.

    Known quirks:
    - Heavy OCR noise from illustrated plates and decorative elements
    - Library stamps (Harvard College Library, Widener)
    - Multiple introductions by various critics
    - Dialogue-heavy prose
    - Chapter/Part markers
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
        """Book-specific cleanup for Works of Charles Dickens."""
        # Remove running headers like "PICKWICK PAPERS" with page numbers
        text = re.sub(
            r"^\s*\d+\s+PICKWICK PAPERS\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*PICKWICK PAPERS\.?\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = _remove_page_furniture(text)

        # Arabic comma pairs are scan substitutions for opening quotation marks.
        text = text.replace('،، Gone!"', '"Gone!"')
        text = text.replace('\n،،\n"Ah,', '\n"Ah,')
        text = text.replace("\n،،\nYou will", '\n"You will')

        # The remaining material after the story is a library due slip.
        due_slip = text.find("\nTHE BORROWER WILL BE CHARGED")
        if due_slip >= 0:
            text = re.sub(r"(?:\n(?:NG|•)\s*)+$", "", text[:due_slip])

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
