"""
Handler for "Introduction to the Study of International Law" by Theodore Dwight Woolsey (1879).

A textbook designed as an aid in teaching and in historical studies.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class InternationalLawWoolsey(BookProcessor):
    """
    Processor for Introduction to the Study of International Law.
    """

    barcode = "32044103157517"
    title = "Introduction to the Study of International Law"
    author = "Woolsey, Theodore Dwight"
    date = "1879"

    notes = """
    Educational text on international law.

    Known quirks:
    - Designed for teaching/study
    - Discussion of neutrality, war, treaties
    - Legal principles and historical examples
    - Running headers likely present
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
        """Book-specific cleanup for Introduction to International Law."""
        import regex as re

        # Running heads alternate between complementary fragments on facing pages.
        # Require an exact observed head next to its Arabic page number so that
        # chapter headings and legal citations with the same words survive.
        running_headers = (
            "APPENDIX II.",
            "BELLIGERENTS AND NEUTRALS.",
            "AND REDRESS OF INJURIES, ETC.",
            "OF THE RELATIONS BETWEEN",
            "RIGHTS OF SELF-DEFENSE",
            "INDEX.",
            "AGENTS OF INTERCOURSE, ETC.",
            "INTERNATIONAL LAW.",
            "RIGHTS OF STATES AS SOVEREIGNTIES.",
            "RELATIONS OF FOREIGNERS, ETC.",
            "APPENDIX I.",
            "THE FORMS AND THE",
            "AND RIGHTS OVER TERRITORY.",
            "AND ESPECIALLY OF TREATIES.",
            "RIGHT OF INTERCOURSE.",
            "OF INTERNATIONAL LAW.",
            "INTRODUCTORY CHAPTER.",
            "STATES' RIGHT OF PROPERTY",
            "OF THE RIGHT OF CONTRACT",
            "APPENDIX II",
            "APPENDIX IL.",
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

        # Standalone section labels were consistently OCRed with "$" for "§".
        # Inline dollar amounts are intentionally outside this exact line rule.
        text = re.sub(r"(?m)^([ \t]*)\$(?=[ \t]*\d{1,3}\.[ \t]*$)", r"\1§", text)
        text = text.replace("medi-\næval Latin", "mediæval Latin")
        text = text.replace("délib-\nérations ultérieures", "délibérations ultérieures")

        return re.sub(r"\n{3,}", "\n\n", text).strip()
