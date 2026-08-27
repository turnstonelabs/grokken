"""
Handler for "An Introduction to Algebra" by Jeremiah Day (1847).

A mathematics textbook, being the first part of a course of mathematics.

Score: 37.4
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "ADDITION.",
        "ALGEBRA",
        "ALGEBRA.",
        "APPLICATION TO GEOMETRY.",
        "ARITHMETICAL PROGRESSION.",
        "COMMON MEASURE.",
        "DIVISION.",
        "EQUATIONS OF CURVES.",
        "EQUATIONS.",
        "EVOLUTION.",
        "FRACTIONS.",
        "GEOMETRICAL PROBLEMS.",
        "GEOMETRICAL PROGRESSION.",
        "INFINITE SERIES.",
        "INVOLUTION OF BINOMIALS.",
        "INVOLUTION.",
        "MATHEMATICAL INFINITY.",
        "MATHEMATICS.",
        "MULTIPLICATION.",
        "NOTATION.",
        "NOTES.",
        "POWERS.",
        "PROPORTION.",
        "QUADRATIC EQUATIONS.",
        "RADICAL QUANTITIES.",
        "RATIO.",
        "SIMPLE EQUATIONS.",
        "VARIATION.",
    }
)
_FOLIO_RANGE = range(1, 333)
_MIN_FOLIO_SEQUENCE = 20


def _remove_page_furniture(text: str) -> str:
    """Remove exact running labels only on a long monotone folio sequence."""
    lines = text.splitlines()
    header_indices = [index for index, line in enumerate(lines) if line.strip() in _RUNNING_HEADERS]
    candidates: list[tuple[int, int, set[int]]] = []
    for index, line in enumerate(lines):
        if not re.fullmatch(r"[ \t]*\d{1,4}[ \t]*", line):
            continue
        headers = {header for header in header_indices if abs(header - index) <= 4}
        value = int(line.strip())
        if headers and value in _FOLIO_RANGE:
            candidates.append((index, value, headers))

    forward = [1] * len(candidates)
    for position, (index, value, _) in enumerate(candidates):
        for prior in range(position - 1, -1, -1):
            prior_index, prior_value, _ = candidates[prior]
            if index - prior_index > 700:
                break
            if 0 < value - prior_value <= 4:
                forward[position] = max(forward[position], forward[prior] + 1)

    backward = [1] * len(candidates)
    for position in range(len(candidates) - 1, -1, -1):
        index, value, _ = candidates[position]
        for following in range(position + 1, len(candidates)):
            following_index, following_value, _ = candidates[following]
            if following_index - index > 700:
                break
            if 0 < following_value - value <= 4:
                backward[position] = max(backward[position], backward[following] + 1)

    clear: set[int] = set()
    for position, (index, value, headers) in enumerate(candidates):
        sequence_length = forward[position] + backward[position] - 1
        ambiguous = any(
            other_index != index and other_value == value and abs(other_index - index) <= 700
            for other_index, other_value, _ in candidates
        )
        if sequence_length >= _MIN_FOLIO_SEQUENCE and not ambiguous:
            clear.update({index, *headers})
    return "\n".join(line for index, line in enumerate(lines) if index not in clear)


class AlgebraDay(BookProcessor):
    """
    Processor for An Introduction to Algebra.
    """

    barcode = "32044097009690"
    title = "An Introduction to Algebra"
    author = "Day, Jeremiah"
    date = "1847"

    notes = """
    Mathematics textbook on algebra.

    Known quirks:
    - Mathematical notation and equations
    - Problem numbers (Prob. 26, etc.)
    - Variables (x, y) that might confuse OCR
    - Running headers like "EQUATIONS"
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1847 text
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Introduction to Algebra."""
        # Discard the scan wrapper and title pages. The first preface is the
        # beginning of the authored text in this copy.
        front_marker = "PREFACE.\nTHE following summary"
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        text = _remove_page_furniture(text)

        # This was the sole remaining word split across a page boundary after
        # the page furniture had been removed.
        text = text.replace("suc-\n\nceeding", "succeeding")

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
