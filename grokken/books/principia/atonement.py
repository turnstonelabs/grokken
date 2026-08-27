"""
Handler for "The Atonement: discourses and treatises" (1859).

A collection of theological discourses by Edwards, Smalley, Maxcy, Emmons,
Griffin, Burge, and Weeks, with an introductory essay by Edwards A. Park.

Score: 39.0 (tied for highest in Principia 34)
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "A MORAL GOVERNMENT.",
        "AGENTS TREATED CONDITIONALLY.",
        "AN ACT OF FREE GRACE.",
        "AN INQUIRY CONCERNING IMPUTATION.",
        "ANSWER TO AN OBJECTION.",
        "APPENDIX.",
        "ATONEMENT NOT RECONCILIATION.",
        "ATONEMENT NOT SECRET.",
        "ATTRIBUTES OF MORAL AGENTS.",
        "CALVIN, WATTS, AND OTHERS.",
        "CHAP. I.]",
        "CHAP. II.]",
        "CHAP. III.]",
        "CHAP. IV.]",
        "CHAP. V.]",
        "CHAP. V.] THE TWO CHARACTERS OF MAN DISTINCT.",
        "CHAP. VI.]",
        "CHAP. VII.]",
        "CHAP. VIII.]",
        "CHAP. X.]",
        "CHAP. XI.]",
        "CHAP. XII.] LOVE EXPRESSED WITHOUT SANCTIFICATION.",
        "CHAP. XV.] REASONS FOR THE GENERAL PROVISION.",
        "CHAP. XVII.]",
        "CHAP. XX.]",
        "CHAP. XXI.]",
        "CONCLUSION.",
        "CONFUSION OF NAMES.",
        "COVENANT OF REDEMPTION.",
        "DIALOGUE ON THE ATONEMENT.",
        "DISCOURSE ON THE ATONEMENT.",
        "EDWARDEAN THEORY OF THE ATONEMENT.",
        "EXPRESSLY FOR ALL.",
        "EXTENT OF THE ATONEMENT.",
        "FIGURATIVE LANGUAGE.",
        "GRACE CONSISTENT WITH ATONEMENT.",
        "GRAND POINT OF DIVISION.",
        "HUMAN AGENCY OVERLOOKED.",
        "IMPORTANCE OF CORRECT LANGUAGE.",
        "INDEX.",
        "INFERENCES AND REFLECTIONS.",
        "INFLUENCE ON LAW.",
        "INFLUENCE ON MEN.",
        "INFLUENCE UPON ALL.",
        "INTRODUCTORY ESSAY.",
        "JUSTIFICATION THROUGH CHRIST,",
        "MATTER OF ATONEMENT.",
        "MEANING OF RIGHTEOUSNESS.",
        "NATURE OF THE ATONEMENT.",
        "NECESSITY OF AN ATONEMENT.",
        "NECESSITY OF ATONEMENT.",
        "NECESSITY OF FAITH.",
        "NECESSITY OF THE ATONEMENT.",
        "NONE BUT BELIEVERS SAVED,",
        "OBEDIENCE OF CHRIST.",
        "ORDER OF DIVINE DECREES.",
        "SCRIPTURAL VIEW.",
        "SCRIPTURE DOCTRINE OF ATONEMENT.",
        "SUFFICIENCY OF CHRIST'S SUFFERINGS.",
        "THE BENEFIT OFFERED TO ALL.",
        "THE OBEDIENCE OF CHRIST.",
        "THE PURCHASE OF CHRIST'S BLOOD.",
        "THROUGH THE SATISFACTION OF CHRIST.",
        "[PART I.",
        "[PART II.",
        "[PART III.",
    }
)
_FOLIO_RANGE = range(1, 596)
_MIN_FOLIO_SEQUENCE = 20


def _folio_value(line: str) -> int | None:
    stripped = line.strip()
    if stripped.isdigit():
        value = int(stripped)
        return value if value in _FOLIO_RANGE else None
    if not re.fullmatch(r"(?i)[ivxlcdm]{1,12}", stripped):
        return None
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for character in reversed(stripped.upper()):
        value = values[character]
        total += -value if value < previous else value
        previous = max(previous, value)
    return total if 1 <= total <= 80 else None


def _remove_page_furniture(text: str) -> str:
    """Remove exact running labels only on a long monotone folio sequence."""
    lines = text.splitlines()
    header_indices = [index for index, line in enumerate(lines) if line.strip() in _RUNNING_HEADERS]
    candidates: list[tuple[int, int, set[int]]] = []
    for index, line in enumerate(lines):
        value = _folio_value(line)
        if value is None:
            continue
        headers = {header for header in header_indices if abs(header - index) <= 4}
        if headers:
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


class Atonement(BookProcessor):
    """
    Processor for The Atonement: discourses and treatises.
    """

    barcode = "HWT5II"
    title = "The Atonement: discourses and treatises"
    author = "Edwards, Smalley, Maxcy, Emmons, Griffin, Burge, Weeks"
    date = "1859"

    notes = """
    Collection of theological discourses on the atonement doctrine.

    Known quirks:
    - Heavy front matter with library stamps, catalog numbers
    - Multiple authors/sections
    - Biblical quotations throughout
    - Footnotes with references
    - Running headers "THE ATONEMENT" or discourse titles
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
        """Book-specific cleanup for The Atonement."""
        front_marker = "INTRODUCTORY ESSAY.\nTHERE is a theory"
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        final_end = text.rfind("\nEND.")
        if final_end >= 0:
            text = text[: final_end + len("\nEND.")]

        text = _remove_page_furniture(text)
        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
