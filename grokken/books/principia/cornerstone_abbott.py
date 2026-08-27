"""
Handler for "The Corner-stone" by Jacob Abbott (1830).

A familiar illustration of the principles of Christian truth.

Score: 36.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "HUMAN DUTY",
        "HUMAN DUTY.",
        "HUMAN NATURE",
        "HUMAN NATURE.",
        "PARDON",
        "PARDON.",
        "PUNISHMENT",
        "PUNISHMENT.",
        "THE CONCLUSION",
        "THE CONCLUSION.",
        "THE CRUCIFIERS",
        "THE CRUCIFIERS.",
        "THE DEITY",
        "THE DEITY.",
        "THE LAST SUPPER.",
        "THE MAN CHRIST JESUS.",
        "THE PARTING COMMAND",
        "THE PARTING COMMAND.",
        "THE PARTING PROMISE.",
    }
)
_CHAPTER_HEADER = re.compile(r"\[?Ch\.\s*(?:\d{1,2}|&)(?:\.\d+)?\.?\]?")
_FOLIO_RANGE = range(14, 361)
_MIN_FOLIO_SEQUENCE = 20


def _is_running_header(line: str) -> bool:
    return line in _RUNNING_HEADERS or _CHAPTER_HEADER.fullmatch(line) is not None


def _remove_page_furniture(text: str) -> str:
    """Remove exact running labels only on a long monotone folio sequence."""
    lines = text.splitlines()
    header_indices = [index for index, line in enumerate(lines) if _is_running_header(line.strip())]
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


class Cornerstone(BookProcessor):
    """
    Processor for The Corner-stone.
    """

    barcode = "AH45Q4"
    title = "The Corner-stone, or, A familiar illustration of Christian principles"
    author = "Abbott, Jacob"
    date = "1830"

    notes = """
    Religious/devotional work by Jacob Abbott (famous for Rollo books).

    Known quirks:
    - Religious/Christian content
    - Discussion of redemption, Jesus Christ
    - Devotional prose style
    - Early date (1830) may mean more OCR issues
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1830 text
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for The Corner-stone."""
        front_marker = "PREFACE.\nTHE following work"
        first_front = text.find(front_marker)
        second_front = text.find(front_marker, first_front + len(front_marker))
        if second_front > 0:
            text = text[second_front:]

        text = _remove_page_furniture(text)
        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
