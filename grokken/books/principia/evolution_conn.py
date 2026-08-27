"""
Handler for "Evolution of To-day" by H. W. Conn (1886).

A summary of the theory of evolution as held by scientists of the present day.

Score: 36.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "EVOLUTION OF TO-DAY.",
        "EVOLUTION OF TO-DA Y.",
        "INTRODUCTION.",
        "SUMMARY.",
        "OCEANIC ISLANDS.",
        "ARE SPECIES STABLE?",
        "HOMOLOGY.",
        "EXPLAINING THE CONTRADICTIONS.",
        "INDIRECT EVIDENCE.",
        "PRESENT AND PAST.",
        "LIMITATION BY BARRIERS.",
        "SPECIFIC CHARACTERS.",
        "NEO-LAMARCKIANISM.",
        "THEORY OF BROOKS.",
        "KNOWLEDGE OF TOOLS, ETC.",
        "THE MORAL SENSE.",
        "MORAL NATURE.",
        "GENERAL SUMMARY.",
    }
)

_SCAN_GARBAGE_LINES = frozenset({"हदर", "蘼", "Ꮓ"})


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


class EvolutionToday(BookProcessor):
    """
    Processor for Evolution of To-day.
    """

    barcode = "HN28C4"
    title = "Evolution of To-day: a summary of the theory of evolution"
    author = "Conn, H. W."
    date = "1886"

    notes = """
    Scientific summary of evolutionary theory.

    Known quirks:
    - Scientific terminology (fossils, species, genera)
    - Discussion of geographical distribution
    - References to migrations, localities
    - Late 19th century scientific prose
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
        """Book-specific cleanup for Evolution of To-day."""
        text = _remove_page_furniture(text)

        # The index is followed by a library return slip.
        due_slip = text.find("\nThis book should be returned to")
        if due_slip >= 0:
            text = text[:due_slip]

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
