"""
Handler for "Church Building" by Ralph Adams Cram (1901).

A study of the principles of architecture in their relation to the church.
The smallest category (Fine Arts) representative.

Score: 37.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "CHANCEL AND ITS FITTINGS",
        "CHAPELS, BAPTISTERIES, ETC.",
        "CHURCH BUILDING",
        "CONCLUSION",
        "DECORATION AND STAINED GLASS",
        "INTRODUCTION",
        "THE ALTAR",
        "THE CATHEDRAL",
        "THE CITY CHURCH",
        "THE COUNTRY CHAPEL",
        "THE VILLAGE CHURCH",
        "VESTIBULE",
    }
)
_FOLIO_RANGE = range(1, 228)
_MIN_FOLIO_SEQUENCE = 10


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


class ChurchBuilding(BookProcessor):
    """
    Processor for Church Building.
    """

    barcode = "32044038386975"
    title = "Church Building: a study of the principles of architecture"
    author = "Cram, Ralph Adams"
    date = "1901"

    notes = """
    Architectural study of church design.

    Known quirks:
    - Figure/plate references (J. D. Sedding, Architect, etc.)
    - Architectural terminology (credence, sedilia, stalls)
    - Roman numeral figure numbers (LXI)
    - Descriptions of church elements
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
        """Book-specific cleanup for Church Building."""
        front_marker = "PREFACE\nTHE greater portion"
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        scan_tail = text.find("\n婴\n")
        if scan_tail >= 0:
            text = text[:scan_tail]

        text = _remove_page_furniture(text)
        text = text.replace("medi-\n\næval", "mediæval")
        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
