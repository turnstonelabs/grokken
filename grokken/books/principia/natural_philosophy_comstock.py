"""
Handler for "A System of Natural Philosophy" by J. L. Comstock (1835).

A natural philosophy (physics) textbook from the early 19th century.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class NaturalPhilosophy(BookProcessor):
    """
    Processor for A System of Natural Philosophy.
    """

    barcode = "32044097047575"
    title = "A System of Natural Philosophy"
    author = "Comstock, J. L."
    date = "1835"

    notes = """
    Early natural philosophy/physics textbook.

    Known quirks:
    - Q&A format (questions and answers)
    - Discussion of light, optics, colors
    - Older scientific terminology
    - May have more OCR issues due to age (1835)
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1835 text
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for A System of Natural Philosophy."""
        import regex as re

        # Exact numbered running heads. Figure labels, formulas, and unnumbered
        # section headings are deliberately outside this rule.
        running_headers = (
            "ASTRONOMY.",
            "ASTRONOMY,",
            "MIRRORS.",
            "PROPERTIES OF BODIES.",
            "ELECTRICITY.",
            "VISION.",
            "GRAVITY.",
            "HYDROSTATICS.",
            "EARTH.",
            "TIME.",
            "LEVER.",
            "WHEEL AND AXLE.",
            "HYDRAULICS.",
            "ACOUSTICS.",
            "OPTICS.",
            "MOON.",
            "BAROMETER.",
            "LENSES.",
            "TELESCOPE.",
            "CENTRE OF GRAVITY.",
            "SCREW.",
            "RAINBOW.",
            "SEASONS.",
            "ECLIPSES.",
            "CURVILINEAR MOTION.",
            "PENDULUM.",
            "PULLEY.",
            "LATITUDE AND LONGITUDE.",
            "MAGNETISM.",
            "RESULTANT MOTION.",
            "MECHANICS.",
            "PNEUMATICS.",
            "PUMP.",
            "FIGURE OF THE EARTH.",
            "PRECESSION OF EQUINOXES.",
            "TIDES.",
            "COLORS.",
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

        # Confirmed local crop/segmentation errors. These are exact phrases so
        # diagram labels, formulas, and historical spelling remain untouched.
        text = text.replace("in Washing\nton College", "in Washington College")
        text = text.replace("along. Bu\non making", "along. But\non making")
        text = text.replace("The re\naction of the atmosphere", "The reaction of the atmosphere")
        text = text.replace("the bel\nlows", "the bellows")
        text = text.replace("moved at alt, for", "moved at all, for")
        text = text.replace("15lbs..", "15 lbs.")
        text = text.replace("sec_Chemistry", "see Chemistry")
        text = text.replace("antartic circle", "antarctic circle")
        text = text.replace("non-conduct\nors", "non-conductors")

        return re.sub(r"\n{3,}", "\n\n", text).strip()
