"""
Handler for "The Works of William E. Channing, D.D." (1875).

Collected works of William Ellery Channing, the prominent Unitarian minister
and theologian. One of the largest books in the Principia 34 at over 1M tokens.

Score: 38.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "ADDRESS ON TEMPERANCE.",
        "ADDRESS ON THE ANNIVERSARY OF",
        "AGAINST CALVINISM.",
        "AND DENUNCIATION IN RELIGION.",
        "CHARACTER OF CHRIST.",
        "CHARGE AT THE ORDINATION",
        "CHARGE FOR THE ORDINATION",
        "CHRISTIAN WORSHIP.",
        "CHRISTIANITY A RATIONAL RELIGION.",
        "CHRISTIANITY CONSIDERED.",
        "DAILY PRAYER.",
        "DEMANDS OF THE AGE ON THE MINISTRY.",
        "DISCOURSE OCCASIONED BY",
        "DISCOURSE ON THE LIFE AND CHARACTER",
        "DUTIES OF THE CITIZEN",
        "EMANCIPATION IN THE BRITISH WEST INDIES.",
        "EMANCIPATION.",
        "EVIDENCES OF CHRISTIANITY.",
        "EVIDENCES OF REVEALED RELIGION.",
        "HONOR DUE TO ALL MEN.",
        "IMITABLENESS OF CHRIST'S CHARACTER.",
        "IMMORTALITY.",
        "IMPORTANCE OF RELIGION TO SOCIETY.",
        "INDEX.",
        "IN TIMES OF TRIAL OR DANGER.",
        "INTRODUCTORY REMARKS.",
        "LETTER ON CATHOLICISM.",
        "LIKENESS TO GOD.",
        "LOVE TO CHRIST.",
        "MEANS OF PROMOTING CHRISTIANITY.",
        "MEMOIR OF JOHN GALLISON, ESQ.",
        "MINISTRY FOR THE POOR.",
        "MOST FAVORABLE TO PIETY.",
        "NOTICE OF REV. S. C. THACHER.",
        "OBJECTIONS TO UNITARIAN",
        "OF NAPOLEON BONAPARTE.",
        "OF REV. R. C. WATERSTON.",
        "OF THE REV. DR. TUCKERMAN.",
        "ON CREEDS.",
        "ON PREACHING TO THE POOR.",
        "ON THE ANNEXATION OF TEXAS",
        "ON THE CHARACTER AND",
        "ON THE ELEVATION OF",
        "ON THE LIFE AND CHARACTER",
        "ON THE SYSTEM OF EXCLUSION",
        "PREACHING CHRIST.",
        "REMARKS ON ASSOCIATIONS.",
        "REMARKS ON EDUCATION.",
        "REMARKS ON NATIONAL LITERATURE.",
        "REMARKS ON THE",
        "SELF-CULTURE.",
        "SELF-DENIAL.",
        "SLAVERY",
        "SLAVERY QUESTION.",
        "SLAVERY.",
        "SPIRITUAL FREEDOM.",
        "THE ABOLITIONISTS.",
        "THE CHRISTIAN MINISTRY.",
        "THE CHURCH.",
        "THE DEATH OF DR. FOLLEN.",
        "THE DUTIES OF CHILDREN.",
        "THE DUTY OF THE FREE STATES.",
        "THE EVIL OF SIN.",
        "THE FUTURE LIFE.",
        "THE GREAT PURPOSE OF CHRISTIANITY.",
        "THE LABORING CLASSES.",
        "THE MORAL ARGUMENT",
        "THE PHILANTHROPIST.",
        "THE PRESENT AGE.",
        "THE SUNDAY-SCHOOL.",
        "THE UNION.",
        "THEOLOGICAL EDUCATION.",
        "TO THE UNITED STATES.",
        "UNITARIAN CHRISTIANITY",
        "UNITARIAN CHRISTIANITY.",
        "WAR.",
        "WRITINGS OF FENELON.",
        "WRITINGS OF MILTON.",
    }
)
_FOLIO_RANGE = range(1, 932)
_MIN_FOLIO_SEQUENCE = 20
_PRESERVE_HYPHENATED = ("anti-slavery",)


def _dehyphenate_channing(text: str) -> str:
    """Preserve independently verified lexical hyphens in this edition."""
    return whitespace.dehyphenate_attested(
        text,
        preserve_hyphenated=_PRESERVE_HYPHENATED,
    )


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


class ChanningWorks(BookProcessor):
    """
    Processor for The Works of William E. Channing.
    """

    barcode = "AH3KTH"
    title = "The Works of William E. Channing, D.D."
    author = "Channing, William Ellery"
    date = "1875"

    notes = """
    Collected theological and philosophical works of William Ellery Channing.

    Known quirks:
    - Very large (1M+ tokens)
    - Theological/philosophical essays
    - Discussion of Calvinism, Unitarianism
    - Multiple essays/sermons collected together
    - Running headers with essay titles
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        _dehyphenate_channing,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Works of William E. Channing."""
        front_marker = "INTRODUCTORY REMARKS.\nTHE following tracts"
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        imprint = text.find("\nCambridge: Press of John Wilson & Son.")
        if imprint >= 0:
            text = text[:imprint]

        text = _remove_page_furniture(text)
        text = text.replace("insti-\n\ntution", "institution")
        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
