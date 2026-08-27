"""
Handler for "The Bible as Literature" by Irving Francis Wood (1914).

An introduction to studying the Bible as a literary work.

Score: 36.8
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "ACTS",
        "AMOS",
        "BOOKS FOR REFERENCE",
        "CORINTHIANS",
        "DANIEL",
        "ECCLESIASTES",
        "EZEKIEL",
        "GENESIS",
        "HAGGAI, ZECHARIAH, AND OBADIAH",
        "HEBREW PROPHECY",
        "HEBREWS",
        "HOSEA",
        "ISAIAH",
        "JEREMIAH",
        "JOB",
        "JUDGES",
        "LETTER TO THE GALATIANS",
        "LETTERS-PAUL'S IMPRISONMENT",
        "LUKE",
        "MALACHI AND JOEL",
        "MARK",
        "MATTHEW",
        "MICAH",
        "PROVERBS",
        "PSALMS",
        "ROMANS",
        "SECOND ISAIAH",
        "THE BIBLE AS LITERATURE",
        "THE BOOKS OF KINGS",
        "THE BOOKS OF NARRATIVE",
        "THE BOOKS OF SAMUEL",
        "THE FOURTH GOSPEL",
        "THE PASTORAL LETTERS",
        "THE REVELATION",
        "THE SHORT STORIES",
        "THE SYNOPTIC PROBLEM",
        "THE TEACHINGS OF JESUS",
        "THE THREE EPISTLES OF JOHN",
    }
)
_FOLIO_RANGE = range(1, 347)
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


class BibleAsLiterature(BookProcessor):
    """
    Processor for The Bible as Literature.
    """

    barcode = "HNU1G9"
    title = "The Bible as Literature: an introduction"
    author = "Wood, Irving Francis"
    date = "1914"

    notes = """
    Literary analysis of the Bible.

    Known quirks:
    - Discussion of biblical genres (proverbs, etc.)
    - Verse references (16. 1-9, 14)
    - Analysis of Hebrew literature structure
    - References to Jehovah, the king
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
        """Book-specific cleanup for The Bible as Literature."""
        front_marker = "PREFACE\nTHIS book is designed"
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        due_slip = text.find("\nJ\n\nS\n\nTHE BORROWER")
        if due_slip >= 0:
            text = text[:due_slip]

        text = _remove_page_furniture(text)
        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
