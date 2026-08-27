"""
Handler for "An Introduction to the Study of the Middle Ages (375-814)"
by Ephraim Emerton (1888).

A historical text covering early medieval history.

Score: 36.8
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class MiddleAges(BookProcessor):
    """
    Processor for Introduction to the Study of the Middle Ages.
    """

    barcode = "HWQXIB"
    title = "An Introduction to the Study of the Middle Ages (375-814)"
    author = "Emerton, Ephraim"
    date = "1888"

    notes = """
    Historical introduction to early medieval period.

    Known quirks:
    - Historical narrative covering 375-814 CE
    - Discussion of Bavaria, nobility, organization
    - Place names and historical figures
    - Academic historical prose
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
        """Book-specific cleanup for Introduction to the Middle Ages."""
        import regex as re

        # The chapter title is repeated as a running head on one side of each
        # opening. Restrict removal to exact observed titles paired with a page
        # number, preserving map labels, chronological tables, and real headings.
        running_headers = (
            "CHARLEMAGNE KING OF THE FRANKS.",
            "RISE OF THE CHRISTIAN CHURCH.",
            "BEGINNINGS OF THE FEUDAL SYSTEM.",
            "GERMANIC IDEAS OF LAW.",
            "MARTEL TO CHARLEMAGNE.",
            "THE FRANKS TO 638.",
            "THE MONKS OF THE WEST.",
            "THE FRANKS FROM",
            "FRANKS AND MOHAMMEDANS, 638–741.",
            "THE GERMANS IN ITALY.",
            "THE TWO RACES.",
            "FOUNDATION OF THE MEDIEVAL EMPIRE.",
            "THE ROMANS TO A.D. 375.",
            "FRANKS AND MOHAMMEDANS, 638-741.",
            "THE INVASION OF THE HUNS.",
            "INDEX.",
            "BREAKING OF THE FRONTIER.",
            "THE BREAKING OF THE",
            "THE VANDALS AND BURGUNDIANS.",
            "FRONTIER BY THE VISIGOTHS.",
        )
        header = "|".join(re.escape(value) for value in running_headers)
        text = re.sub(
            rf"(?m)^(?:"
            rf"[ \t]*\d{{1,4}}[ \t]*\n(?:[ \t]*\n)?[ \t]*(?:{header})[ \t]*"
            rf"|[ \t]*(?:{header})[ \t]*\n(?:[ \t]*\n)?[ \t]*\d{{1,4}}[ \t]*"
            rf")$",
            "",
            text,
        )

        # Confirmed English-word OCR substitutions; map labels are left alone.
        text = text.replace("A nátive duke", "A native duke")
        text = text.replace("tho borders of Italy", "the borders of Italy")

        return re.sub(r"\n{3,}", "\n\n", text).strip()
