"""
Handler for "A Complete Manual of English Literature" by Thomas B. Shaw (1867).

A comprehensive guide to English literature.

Score: 37.9
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

# Exact recurrent labels verified beside page folios in this two-column edition.
_RUNNING_HEADERS = frozenset(
    {
        "NOTES AND ILLUSTRATIONS.",
        "NOTES AND ILLUSTRATIONS:",
        "AMERICAN LITERATURE.",
        "A SKETCH OF",
        "SHAKSPEARE.",
        "THE AGE OF CHAUCER.",
        "JOHN MILTON.",
        "WALTER SCOTT.",
        "THE MODERN NOVELISTS.",
        "THE GREAT NOVELISTS.",
        "THE DAWN OF THE DRAMA.",
        "THE SHAKSPEARIAN DRAMATISTS. [CHAP. VIII.",
        "THE DAWN OF ROMANTIC POETRY. [CHAP. XIX.",
        "NEW DRAMA AND CORRECT POETS. [CHAP. XIII.",
        "PHILOSOPHY AND PROSE LITERATURE. [CHAP. V.",
        "POPE, SWIFT, AND AUGUSTAN POETS. [CHAP. XV.",
        "THE AGE OF THE RESTORATION. [CHAP. XII.",
        "THE AGE OF THE RESTORATION.",
        "THE SECOND REVOLUTION.",
        "THE ELIZABETHAN POETS.",
        "THE ESSAYISTS.",
        "PROSE LITERATURE.",
        "ORIGIN OF THE ENGLISH",
        "LANGUAGE AND LITERATURE.",
        "FROM THE DEATH OF CHAUCER",
        "THEOLOGICAL WRITERS.",
        "MORAL WRITERS.",
        "POLITICAL WRITERS.",
        "HISTORICAL WRITERS.",
        "LORD BACON.",
        "LORD BYRON.",
        "ROBERT SOUTHEY.",
        "THOMAS MOORE.",
        "WILLIAM WORDSWORTH.",
        "JONATHAN SWIFT.",
        "ALEXANDER POPE.",
        "JOHN DRYDEN.",
        "JOHN BUNYAN.",
        "JOHN LOCKE.",
        "JOSEPH ADDISON.",
        "SPENSER.",
        "EARLY THEATRES.",
        "INDEX TO ENGLISH LITERATURE.",
        "[CHAP. I.",
        "[CHAP. II.",
        "[CHAP. III.",
        "[CHAP. IV.",
        "[CHAP. VI.",
        "[CHAP. VII.",
        "[CHAP. X.",
        "[CHAP. XI.",
        "[CHAP. XII.",
        "[CHAP. XIV.",
        "[CHAP. XVI.",
        "[CHAP. XVII.",
        "[CHAP. XVIII.",
        "[CHAP. XIX.",
        "[CHAP. XX.",
        "[CHAP. XXI.",
        "[CHAP. XXII.",
        "[CHAP. XXIII.",
        "[CHAP. XXIV.",
        "CHAP. I.]",
        "CHAP. II.]",
        "CHAP. III.]",
        "A. D. 1066.]",
        "A. D. 1400.]",
        "A. D. 1400-1558.] TO THE AGE OF ELIZABETH.",
        "A. D. 1580.]",
        "A. D. 1561-1626.]",
        "A. D. 1564-1616.]",
        "A. D. 1608-1674.]",
        "A. D. 1608-1674-]",
        "A. D. 1628-1688.]",
        "A. D. 1631-1700.]",
        "A. D. 1667-1745.]",
        "A. D. 1672-1719.]",
        "A. D. 1771-1832.]",
    }
)

_SCAN_GARBAGE_LINES = frozenset(
    {
        "៥",
        "ザ",
        "Ꮟ",
        "ܢ",
        "ཏཱ*",
        "་",
        "છે.",
        "รา",
        "ท",
        "દેવશ",
        "رکیه",
        "怎",
        "كم",
        "क",
        "१",
        "は",
    }
)


def _remove_page_furniture(text: str) -> str:
    """Remove exact recurrent running labels attached to printed folios."""
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


class EnglishLiterature(BookProcessor):
    """
    Processor for A Complete Manual of English Literature.
    """

    barcode = "HWPLDT"
    title = "A Complete Manual of English Literature"
    author = "Shaw, Thomas B."
    date = "1867"

    notes = """
    Literary criticism and history of English literature.

    Known quirks:
    - Discussion of various literary works and authors
    - Literary analysis and criticism
    - References to classical and English literature
    - May contain poetry quotations
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
        """Book-specific cleanup for Manual of English Literature."""
        # Two small illustration fragments interrupt otherwise continuous prose.
        text = re.sub(
            r"(chapters, the first of which he wrote thrice, and the second twice over,)"
            r"\n[\s\S]*?\n(?=A\. D\. 1737-1794\.\])",
            r"\1\n",
            text,
        )
        text = re.sub(
            r"(- every feature of his character heightens the charm of this most "
            r"fascinating book\.)"
            r"\n[\s\S]*?\n(?=CHAP\. XVIII\.\])",
            r"\1\n",
            text,
        )
        text = _remove_page_furniture(text)

        # Cyrillic confusables occur only in these English small-cap names.
        replacements = {
            "Sтow": "STOW",
            "Toм BROWN": "TOM BROWN",
            "РоMFRET": "POMFRET",
            "POмfret": "POMFRET",
            "Ноок.": "HOOK.",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)

        # Clearing a folio exposes one verified split Latin title.
        text = text.replace("Ro-\n\nmanorum", "Romanorum")

        # The final lines are a library due slip, not part of the index.
        due_slip = text.find("\nThis book should be returned to")
        if due_slip >= 0:
            text = text[:due_slip]

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
