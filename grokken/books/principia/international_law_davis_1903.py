"""
Handler for "The Elements of International Law" by George B. Davis (1903 edition).

An alternate edition of Davis's legal textbook, with an account of its origin.

Score: 37.8
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class InternationalLawDavis1903(BookProcessor):
    """
    Processor for The Elements of International Law (1903).
    """

    barcode = "HWQTYU"
    title = "The Elements of International Law; with an account of its origin"
    author = "Davis, George B."
    date = "1903"

    notes = """
    Later edition of Davis's international law textbook.

    Known quirks:
    - Extensive footnotes with legal citations
    - References to Pradier-Fodéré, Halleck, Phillimore, etc.
    - Legal terminology and case references
    - Running headers possible
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
        """Book-specific cleanup for Elements of International Law (1903)."""
        import regex as re

        # The scan alternates the book title and chapter title as running heads.
        # Match only exact, observed heads paired with an Arabic page-number line;
        # the same wording in the table of contents or at a chapter opening is kept.
        running_headers = (
            "THE ELEMENTS OF INTERNATIONAL LAW",
            "THE LAW OF WAR",
            "NEUTRALITY",
            "STATES AND THEIR ESSENTIAL ATTRIBUTES",
            "THE RIGHT OF LEGATION",
            "NATIONAL CHARACTER",
            "TREATIES AND CONVENTIONS",
            "MARITIME CAPTURE",
            "THE CONFLICT OF INTERNATIONAL RIGHTS",
            "BLOCKADE-BREACH OF BLOCKADE",
            "PRIVATE INTERNATIONAL LAW",
            "RIGHTS-COMITY-CEREMONIAL",
            "APPENDIX E",
            "APPENDIX A",
            "INDEX",
            "APPENDIX F",
            "CONTRABAND OF WAR",
            "APPENDIX B",
            "THE RIGHT OF SEARCH",
            "DEFINITION AND HISTORY",
            "EXTRADITION",
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

        # Confirmed OCR variants in citations and the naturalization-treaty date.
        # A single dollar sign is retained because this book also quotes money.
        text = text.replace("$$", "§§")
        text = re.sub(r"(?m)^([ \t]*)\$(?=[ \t]*\d{1,3}\.[ \t]*$)", r"\1§", text)
        text = text.replace("Exchange,7", "Exchange, 7")
        text = text.replace("pp.99", "pp. 99")
        text = text.replace("and Norway, May 56, 1869", "and Norway, May 26, 1869")
        text = re.sub(r"(?m)^\* wwwwwww$", "", text)

        return re.sub(r"\n{3,}", "\n\n", text).strip()
