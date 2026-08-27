"""
Handler for "The Elements of International Law" by George B. Davis (1900).

A legal textbook on international law principles.

Score: 37.9
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "THE ELEMENTS OF INTERNATIONAL LAW",
        "DEFINITION AND HISTORY",
        "STATES AND THEIR ESSENTIAL ATTRIBUTES",
        "RIGHTS-COMITY-CEREMONIAL",
        "NATIONAL CHARACTER",
        "THE RIGHT OF LEGATION",
        "THE LAW OF WAR",
        "CONTRABAND OF WAR",
        "BLOCKADE-BREACH OF BLOCKADE",
        "THE RIGHT OF SEARCH",
        "MARITIME CAPTURE",
        "NEUTRALITY",
        "THE CONFLICT OF INTERNATIONAL RIGHTS",
        "PRIVATE INTERNATIONAL LAW",
        "EXTRADITION",
        "TREATIES AND CONVENTIONS",
        "APPENDIX A",
        "APPENDIX B",
        "APPENDIX E",
        "APPENDIX F",
        "INDEX",
    }
)

_SCAN_GARBAGE_LINES = frozenset({"གགགག གཤྩ་ŁŁ$$", "の"})


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


class InternationalLawDavis1900(BookProcessor):
    """
    Processor for The Elements of International Law (1900).
    """

    barcode = "32044103157418"
    title = "The Elements of International Law"
    author = "Davis, George B."
    date = "1900"

    notes = """
    Legal textbook on international law.

    Known quirks:
    - Legal citations and references
    - Footnotes with case references
    - Discussion of war, treaties, neutrality
    - Formal legal prose
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
        """Book-specific cleanup for Elements of International Law."""
        text = _remove_page_furniture(text)

        # Removing page furniture exposes two inspected split words.
        text = text.replace("Phi-\n\nlology", "Philology")
        text = text.replace("de-\n\ntain", "detain")

        # The remaining lines after the explicit terminator are a library plate.
        end = text.find("\nTHE END")
        if end >= 0:
            text = text[: end + len("\nTHE END")]

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
