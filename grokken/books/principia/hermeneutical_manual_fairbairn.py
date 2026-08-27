"""
Handler for "Hermeneutical Manual" by Patrick Fairbairn (1859).

An introduction to the exegetical study of the Scriptures.

Score: 37.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "NEW TESTAMENT GREEK.",
        "THE CHARACTERISTICS OF",
        "SCRIPTURAL DESIGNATIONS",
        "IN NEW TESTAMENT SCRIPTURE.",
        "GENERAL RULES FOR INTERPRETATION OF",
        "TRUE AND FALSE ACCOMMODATION.",
        "THE SUBJECT OF PARALLELISM",
        "THE TWO GENEALOGIES OF CHRIST.",
        "PARTICULAR WORDS AND PASSAGES.",
        "COLLATERAL SOURCES FOR EXPLAINING",
        "THE NEW TESTAMENT WRITINGS.",
        "MORE EXACTLY DEFINED.",
        "TROPICAL PASSAGES.",
        "PROPER METHOD OF INTERPRETING",
        "THE NAMES OF CHRIST",
        "AND DOCTRINE OF ANGELS.",
        "TERMS EXPRESSIVE OF",
        "ANTAGONISTIC RELATIONS TO CHRIST.",
        "RENOVATION ACCOMPLISHED BY THE GOSPEL.",
        "IMPORT AND USE",
        "IMPORT AND USE OF",
        "THE USE OF βαπτίζω",
        "THE USE OF βαπτίζω.",
        "AND ITS COGNATES.",
        "TERMS INDICATIVE OF THE",
        "OF HADES IN SCRIPTURE.",
        "HADES IN SCRIPTURE.",
        "RELIGION OF THE OLD TESTAMENT.",
        "RELATION OF THE OLD TO THE NEW",
        "RESPECT TO BE HAD TO THE",
        "OLD TESTAMENT IN THE NEW.",
        "THE PARABLES OF CHRIST",
        "AND THEIR INTERPRETATION.",
        "PRESIDENCY OF CYRENIUS, LUKE II. 2.",
        "PARASKEUE AND PASCHA",
        "AND TIME OF THE LAST PASSOVER.",
        "ST. MATTHEW'S GOSPEL.",
        "ST. LUKE'S GOSPEL.",
        "ROMANS.",
        "HEBREWS.",
        "ACTS OF THE APOSTLES.",
        "EPHESIANS.",
        "THE ORIGINAL LANGUAGE OF",
        "THE NEW TESTAMENT.",
        "ANALOGY OF THE FAITH.",
        "MATT. I. 23; ISA. VII. 14.",
        "MATT. XXVII. 9, 10; ZECH. XI. 13.",
        "INDEX OF SUBJECTS.",
        "APPENDIX.",
        "GENERAL RESULT.",
    }
)

_SCAN_GARBAGE_LINES = frozenset({"ܕ", "مه", "हे", "Ꮓ", "JLECCO"})


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


class HermeneuticalManual(BookProcessor):
    """
    Processor for Hermeneutical Manual.
    """

    barcode = "HNVJ7R"
    title = "Hermeneutical Manual: Introduction to the exegetical study of Scripture"
    author = "Fairbairn, Patrick"
    date = "1859"

    notes = """
    Biblical hermeneutics/interpretation manual.

    Known quirks:
    - Biblical references and Greek/Hebrew terms
    - Discussion of Jesus, resurrection, Scripture
    - Theological terminology
    - References to followers, disciples
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
        """Book-specific cleanup for Hermeneutical Manual."""
        text = _remove_page_furniture(text)

        # The base dehyphenator is deliberately ASCII-only. This volume's 58
        # remaining cases are all inspected Greek words split at line endings.
        text = re.sub(r"(?<=[\p{L}\p{M}])-\n[ \t]*(?=\p{Greek})", "", text)

        # Removing folios exposes four otherwise ordinary page-break splits.
        for source, target in {
            "hea-\n\nven": "heaven",
            "Gos-\n\npels": "Gospels",
            "misinter-\n\npreted": "misinterpreted",
            "Testa-\n\nment": "Testament",
        }.items():
            text = text.replace(source, target)

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
