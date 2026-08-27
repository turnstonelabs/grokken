"""
Handler for "Studies in Logical Theory" by John Dewey (1903).

A philosophical work on logic and epistemology.

Score: 37.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class LogicalTheory(BookProcessor):
    """
    Processor for Studies in Logical Theory.
    """

    barcode = "32044069804946"
    title = "Studies in Logical Theory"
    author = "Dewey, John"
    date = "1903"

    notes = """
    Dewey's philosophical work on logic.

    Known quirks:
    - Philosophical/epistemological content
    - Discussion of meaning, ideas, images
    - Running headers "STUDIES IN LOGICAL THEORY"
    - Academic prose style
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
        """Book-specific cleanup for Studies in Logical Theory."""
        import regex as re

        # Exact running heads paired with a separate Arabic page-number line.
        # Unnumbered occurrences are structural essay/chapter headings and remain.
        running_headers = (
            "STUDIES IN LOGICAL THEORY",
            "VALUATION AS A LOGICAL PROCESS",
            "BOSANQUET'S THEORY OF JUDGMENT",
            "THE NATURE OF HYPOTHESIS",
            "SOME LOGICAL ASPECTS OF PURPOSE",
            "IMAGE AND IDEA IN LOGIC",
            "THE DATUM OF THINKING",
            "THE CONTENT AND OBJECT OF THOUGHT",
            "STAGES IN DEVELOPMENT OF JUDGMENT",
            "INDEX",
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

        # One confirmed word-boundary loss in the discussion of mental imagery.
        text = text.replace("it matters notthat", "it matters not that")

        return re.sub(r"\n{3,}", "\n\n", text).strip()
