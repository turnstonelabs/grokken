"""
Handler for "The Student's Chaucer" (1895).

A complete edition of Geoffrey Chaucer's works. The largest book in the
Principia 34 at over 1M tokens.

Score: 37.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "A. The Knightes Tale.",
        "A. The Milleres Tale.",
        "A. The Prologue.",
        "A. The Reves Tale.",
        "Appendix.",
        "B. The Monkes Tale.",
        "B. The Tale of Melibeus.",
        "BOOK I.]",
        "BOOK II.]",
        "BOOK III.]",
        "BOOK IV.]",
        "BOOK V.]",
        "E. The Clerkes Tale.",
        "E. The Marchantes Tale.",
        "FRAGMENT A.]",
        "FRAGMENT B.]",
        "FRAGMENT C.]",
        "Glossarial Ender.",
        "Glossarial Inder.",
        "Glossarial Index.",
        "I. The Persones Tale.",
        "Prologue. (Two Versions.)",
        "The Astrolabe: Part II.",
        "The Canterbury Tales.",
        "The Hous of Fame.",
        "The Hour of Fame.",
        "The Legend of Good Women.",
        "The Minor Poems.",
        "The Romaunt of the Rose.",
        "Troilus and Criseyde.",
        "[BOOK II.",
        "[BOOK III.",
        "[BOOK IV.",
        "[BOOK V.",
        "[FRAGMENT A.",
        "[FRAGMENT B.",
        "[FRAGMENT C.",
    }
)
_FOLIO_RANGE = range(1, 733)
_MIN_FOLIO_SEQUENCE = 15


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


class StudentChaucer(BookProcessor):
    """
    Processor for The Student's Chaucer.
    """

    barcode = "HWKBVP"
    title = "The Student's Chaucer, being a complete edition of his works"
    author = "Chaucer, Geoffrey"
    date = "1895"

    notes = """
    Complete works of Geoffrey Chaucer. Largest book in the collection.

    Known quirks:
    - Middle English text
    - Latin phrases (Explicit tercia pars, Sequitur pars quarta)
    - Poetry formatting with line numbers
    - Very large (1M+ tokens)
    - Archaic spelling throughout
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for older text
        # Note: careful with dehyphenation due to poetry
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for The Student's Chaucer."""
        front_marker = "INTRODUCTION.\nLIFE OF CHAUCER."
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        final_end = text.rfind("\nTHE END.")
        if final_end >= 0:
            text = text[: final_end + len("\nTHE END.")]

        text = _remove_page_furniture(text)
        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
