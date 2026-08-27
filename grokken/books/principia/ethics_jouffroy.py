"""
Handler for "Introduction to Ethics" by Theodore Jouffroy (1840).

A philosophical work including a critical survey of moral systems.
Translated from French.

Score: 38.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "JOUFFROY.",
        "JOUFFROY,",
        "THE FACTS OF MAN'S MORAL NATURE.",
        "SYSTEM OF NECESSITY.",
        "SYSTEM OF MYSTICISM.",
        "SYSTEM OF PANTHEISM.",
        "SYSTEM OF SKEPTICISM.",
        "REFUTATION OF SKEPTICISM.",
        "THE SELFISH SYSTEM.",
        "THE SELFISH SYSTEM. HOBBES.",
        "HOBBES.",
    }
)

_SCAN_GARBAGE_LINES = frozenset(
    {
        "ཝཱ",
        "ང་ས་པ་ ང་ ངས་པ་",
        "८",
        "હ ર ર",
        "૨૭",
        "૧",
        "ንጹ",
        "را",
        "の",
        "اهیر هم",
        "典",
        "སྦྱིནདོ",
        "より",
        "کریں",
        "こさん",
        "རྙྭ་རྙྭ་ཏ་",
        "རྩྭ་རྩྭ་ཏ་",
        "爨",
        "に",
        "Ꮓ",
        "ગ",
        "У",
        "ま",
        "༡༤',5,",
        "སུནིཡ॰ }}",
    }
)

_VOLUME_SIGNATURES = frozenset("BCDEFGHIKLMNPRSTUVWXY")


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

    # This volume prints ``VOL. I.`` above a recurring alphabetic gathering
    # signature.  Remove only those exact pairs; the title-page ``VOL. I.``
    # and unpaired headings remain content.
    for index, line in enumerate(lines):
        if line.strip() != "VOL. I.":
            continue
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        decoration: int | None = None
        if cursor < len(lines) and lines[cursor].strip() in {"-", "+"}:
            decoration = cursor
            cursor += 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
        if cursor >= len(lines) or lines[cursor].strip() not in _VOLUME_SIGNATURES:
            continue
        clear.update({index, cursor})
        if decoration is not None:
            clear.add(decoration)
        trailing = cursor + 1
        while trailing < len(lines) and not lines[trailing].strip():
            trailing += 1
        if trailing < len(lines) and lines[trailing].strip() in {"-", "+"}:
            clear.add(trailing)
    return "\n".join(line for index, line in enumerate(lines) if index not in clear)


class IntroductionToEthics(BookProcessor):
    """
    Processor for Introduction to Ethics.
    """

    barcode = "AH3HJZ"
    title = "Introduction to Ethics: including a critical survey of moral systems"
    author = "Jouffroy, Theodore"
    date = "1840"

    notes = """
    French philosophical work on ethics, translated to English.

    Known quirks:
    - Philosophical/metaphysical content
    - Discussion of various moral systems
    - Dense prose style typical of 19th century philosophy
    - References to Spinoza, other philosophers
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1840 text
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Introduction to Ethics."""
        # Handwritten/library scan material precedes the actual title page.
        start = text.find("SPECIMENS\nOF\nFOREIGN STANDARD LITERATURE.")
        if start >= 0:
            text = text[start:]

        # A Cyrillic OCR substitution occurs in the otherwise Latin title page.
        text = re.sub(r"(?m)^то$", "TO", text)
        text = _remove_page_furniture(text)

        # The volume explicitly ends here; the remainder is scanner/library noise.
        end = text.find("\nEND OF VOL. I.")
        if end >= 0:
            text = text[: end + len("\nEND OF VOL. I.")]

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
