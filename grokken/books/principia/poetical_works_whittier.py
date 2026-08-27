"""
Handler for "The Complete Poetical Works of John Greenleaf Whittier" (1873).

Collected poetry of the American Quaker poet and abolitionist.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class WhittierPoetry(BookProcessor):
    """
    Processor for The Complete Poetical Works of John Greenleaf Whittier.
    """

    barcode = "HWK6N4"
    title = "The Complete Poetical Works of John Greenleaf Whittier"
    author = "Whittier, John Greenleaf"
    date = "1873"

    notes = """
    Collected poetry of John Greenleaf Whittier.

    Known quirks:
    - Poetry formatting (line breaks matter)
    - Rhyme schemes and meter
    - Various poem lengths and styles
    - May need careful handling of line breaks
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        # Note: NOT using dehyphenate aggressively for poetry
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Whittier's Poetical Works."""
        import regex as re

        # The collection/section title is repeated at page boundaries. Pairing
        # an exact observed title with its page-number line avoids deleting poem
        # titles, contents entries, or any verse line with the same wording.
        running_headers = (
            "MISCELLANEOUS.",
            "VOICES OF FREEDOM.",
            "POEMS AND LYRICS.",
            "THE TENT ON THE BEACH.",
            "MISCELLANEOUS POEMS.",
            "MOGG MEGONE.",
            "LEGENDARY.",
            "HOME BALLADS.",
            "OCCASIONAL POEMS.",
            "THE PENNSYLVANIA PILGRIM.",
            "THE BRIDAL OF PENNACOOK.",
            "BALLADS.",
            "NOTES.",
            "SONGS OF LABOR.",
            "THE CHAPEL OF THE HERMITS.",
            "THE PANORAMA.",
            "LATER POEMS.",
            "IN WAR TIME.",
            "SNOW-BOUND.",
            "AMONG THE HILLS.",
            "MIRIAM.",
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

        # Five sampled print-wrap splits have unambiguous lexical joins. Keep
        # every other verse line and hyphen untouched.
        text = text.replace("autumn's ris-\ning blast", "autumn's rising blast")
        text = text.replace("smothered thun-\nder,", "smothered thunder,")
        text = text.replace("loved and cher-\nished", "loved and cherished")
        text = text.replace("a hid-\nden fire", "a hidden fire")
        text = text.replace("chil-\ndren yet", "children yet")

        return re.sub(r"\n{3,}", "\n\n", text).strip()
