"""
Handler for "The Federalist" (1864 reprint).

A collection of essays written in favor of the new Constitution by
Alexander Hamilton, James Madison, and John Jay.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_PRESERVE_HYPHENATED = frozenset(
    {
        "book-form",
        "copy-right",
        "dear-bought",
        "eighty-four",
        "fellow-creature",
        "hand-writing",
        "hard-earned",
        "long-continued",
        "ninety-six",
        "non-manufacturing",
        "over-supply",
        "poll-taxes",
        "pre-existing",
        "re-eligibility",
        "seventy-nine",
        "sixty-eight",
        "title-page",
        "twenty-eighth",
        "twenty-fifth",
        "well-informed",
        "well-known",
        "well-regulated",
    }
)
_REJECT_PAGE_GAP_JOINS = frozenset({"arcontained", "interas"})
_VERIFIED_RESIDUAL_WRAP_JOINS = {
    "Foder-\n\nal": "Foderal",
    "pro-\n\nfessing": "professing",
    "trouble-\nsome": "troublesome",
    "trouble-\n\nsome": "troublesome",
    "geome-\n\ntricians": "geometricians",
    "pau-\n\npers": "paupers",
    "inter-\n\ndicts": "interdicts",
    "de-\n\ngeneracy": "degeneracy",
    "in-\n\nquisitors": "inquisitors",
    "Fod-\neral": "Foderal",
}


def _dehyphenate_federalist(text: str) -> str:
    """Use same-book plus independent Dawson/Gutenberg spelling evidence."""
    return whitespace.dehyphenate_attested(
        text,
        preserve_hyphenated=_PRESERVE_HYPHENATED,
    )


def _dehyphenate_federalist_page_gaps(text: str) -> str:
    """Resolve attested page wraps except independently rejected layout collisions."""
    return whitespace.dehyphenate_attested_page_gaps(
        text,
        preserve_hyphenated=_PRESERVE_HYPHENATED,
        reject_joined=_REJECT_PAGE_GAP_JOINS,
    )


class Federalist(BookProcessor):
    """
    Processor for The Federalist.
    """

    barcode = "32044072043805"
    title = "The Federalist: a collection of essays in favor of the new Constitution"
    author = "Hamilton, Madison, Jay"
    date = "1864"

    notes = """
    The Federalist Papers - foundational American political philosophy.

    Known quirks:
    - Political philosophy and constitutional argument
    - Running headers "The Federalist."
    - Discussion of Confederation, Convention
    - Formal 18th century prose style
    """

    transforms = [
        # Encoding cleanup
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        # Typography
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        # OCR fixes
        ocr.fix_common_errors,
        ocr.fix_long_s,  # 1864 reprint of 1788 text
        # Whitespace
        _dehyphenate_federalist,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """
        Book-specific cleanup for The Federalist.

        1. Strips front matter (library stamps, title page, copyright, advertisement, TOC)
        2. Strips back matter (library stamps after "END OF VOL. I.")
        3. Fixes book-specific OCR errors (Jáy, œ ligatures, garbage chars)
        4. Removes running headers in all variant forms
        5. Removes VOL. I. section markers and standalone page numbers
        6. Reflows paragraphs broken by OCR line breaks
        """
        import regex as re

        # === STRIP FRONT MATTER ===
        # Content starts with "INTRODUCTION." (the section header for the editor's
        # introduction by Henry B. Dawson). Everything before is library stamps,
        # title page, copyright, dedication, Advertisement, and Table of Contents.
        front_match = re.search(r"^INTRODUCTION\.\s*$", text, re.MULTILINE)
        if front_match:
            text = text[front_match.start() :]

        # === STRIP BACK MATTER ===
        # Book ends with "END OF VOL. I." followed by library stamps/garbage
        end_match = re.search(r"END OF VOL\.\s*I\.\s*\n", text)
        if end_match:
            text = text[: end_match.end()]

        # === BOOK-SPECIFIC OCR FIXES ===

        # "Jáy" is a consistent OCR misread of "Jay" in both title- and
        # upper-case settings.
        text = text.replace("Jáy", "Jay").replace("JÁY", "JAY")

        # Expand œ/Œ ligatures per typography.py guidance for book-specific post_process.
        # Case-aware: Œ before uppercase → OE (FŒDERAL → FOEDERAL),
        # otherwise Œ → Oe, œ → oe
        text = re.sub(r"\u0152(?=[A-Z])", "OE", text)
        text = text.replace("\u0152", "Oe").replace("\u0153", "oe")

        # Normalize ornamental quote marks to ASCII
        text = text.replace("\u275d", '"').replace("\u275e", '"')

        # Fix Cyrillic/Greek homoglyphs (OCR confuses visually similar scripts)
        text = text.replace("\u03a4\u039f", "TO")  # Greek ΤΟ → TO
        text = text.replace("\u03a4\u03bf", "To")  # Greek Το → To
        text = text.replace("\u0410", "A")  # Cyrillic А → A (ACHEUS)
        # Cyrillic м → m; then fix mangled proper names where it should be M
        text = text.replace("\u043c", "m")
        text = text.replace("RomULUS", "ROMULUS")
        text = re.sub(r"THOm-?\n?AS\b", "THOMAS", text)

        # Remove non-Latin script OCR garbage (Tibetan, Arabic, Korean, Thai, CJK,
        # and remaining Greek/Cyrillic chars that aren't Latin homoglyphs)
        text = re.sub(
            r"[\u0370-\u03ff\u0400-\u04ff\u0600-\u06ff\u0e00-\u0e7f"
            r"\u0f00-\u0fff\u4e00-\u9fff\uac00-\ud7af\u3130-\u318f]",
            "",
            text,
        )

        # Fix dot-below OCR artifact: ị → i (in "whịch" etc.)
        text = text.replace("\u1ecb", "i")

        # Fix superscript digits (OCR artifacts from split capitals at page boundaries).
        # Rejoin drop-cap splits: A¹\nFTER → AFTER. Requires the capital to be at
        # line start and the continuation to be 2+ uppercase chars (avoids joining
        # a footnote superscript at end of a word with a new line).
        text = re.sub(
            r"(?<=\n)([A-Z])[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]+\n([A-Z]{2,})",
            r"\1\2",
            text,
        )
        # Then remove any remaining superscript digits (footnote markers etc.)
        text = re.sub(r"[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]", "", text)

        # Remove bullet and symbol OCR artifacts
        text = re.sub(r"[\u2022\u26ab\u25bc\u00bf]", "", text)  # •⚫▼¿
        text = text.replace("\u2758", "|")  # ❘ → |
        text = text.replace("\u00b7", ".")  # · → .

        # Normalize ellipsis runs (dot leaders in TOC sections)
        text = re.sub(r"\u2026+", "...", text)
        text = re.sub(r"\.{4,}", "...", text)

        # === REMOVE RUNNING HEADERS ===
        # Headers appear as "The F[oe]deralist." / "Introduction." / "Contents." /
        # "Advertisement." in 4 positional forms, plus all-caps "THE FEDERALIST."

        header = r"(The\s+F[oe]{0,2}deralist|Introduction|Contents|Advertisement)\."

        # Pattern A: Page number on own line, then header on next line
        # Allow optional leading +/* from OCR errors (e.g. "+3" for "43")
        text = re.sub(rf"\n[+*]?\d{{1,4}}\n{header}\n", "\n", text)

        # Pattern B: Header on own line, then page number on next line
        text = re.sub(rf"\n{header}\n\d{{1,4}}\n", "\n", text)

        # Pattern C: Page number + header on same line
        text = re.sub(rf"^\s*\d+\s+{header}\s*$", "", text, flags=re.MULTILINE)

        # Pattern D: Header + page number on same line
        text = re.sub(rf"^\s*{header}\s+\d+\s*$", "", text, flags=re.MULTILINE)

        # All-caps "THE FEDERALIST." running headers (not essay headers which
        # include "No. X", so those are preserved)
        text = re.sub(r"^\s*THE\s+FEDERALIST\.?\s*$", "", text, flags=re.MULTILINE)

        # Standalone running header lines (no adjacent page number).
        # Title-case only — the all-caps "INTRODUCTION." section header is preserved.
        text = re.sub(
            r"^\s*(Introduction|Contents|Advertisement)\.\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # === REMOVE VOL. I. SECTION MARKERS ===
        # These appear mid-text as "VOL. I.\n{page_id}\n" where page_id may be a
        # digit, a letter (b, c, d, e, g, h in the introduction), or absent.
        # Negative lookbehind preserves "END OF VOL. I."
        text = re.sub(r"(?<!END OF )VOL\.\s*I\.\s*\n", "\n", text)

        # === REMOVE STANDALONE PAGE NUMBERS ===
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        # === REMOVE LETTER PAGE IDENTIFIERS ===
        # The introduction uses single-letter page IDs (b, c, d, e, g, h)
        text = re.sub(r"^\s*[a-h]\s*$", "", text, flags=re.MULTILINE)

        # === REMOVE ROMAN NUMERAL PAGE NUMBERS ===
        # The introduction uses roman numerals (ii, iii, iv, etc.).
        # Require 2+ chars to avoid matching the pronoun "I" or single letters.
        # Case-consistent to avoid matching words like "ill" or "Civil".
        text = re.sub(
            r"^\s*(?:[ivxlc]{2,12}|[IVXLC]{2,6})\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Five exact page seams were historically corrupted when dehyphenation
        # crossed a Roman page identifier. Repair both the source-preserving form
        # and the legacy fused form so post_process remains backward-compatible.
        text = re.sub(r"\bHAMIL-\n(?:[ \t]*\n)*\"?TON\b", "HAMILTON", text)
        text = re.sub(r'\bex-\n(?:[ \t]*\n)*"?pression\b', "expression", text)
        text = re.sub(
            r'\bMADI-\n(?:[ \t]*\n)*(?:-[ \t]*\n)?"?SON\b',
            "MADISON",
            text,
        )
        text = re.sub(r"\bdis(?:c)?-\n(?:[ \t]*\n)*agreement\b", "disagreement", text)
        text = re.sub(
            r"\bbec-\n(?:[ \t]*\n)*(?:Essay\. Page[ \t]*\n)?havior\b",
            "behavior",
            text,
        )
        text = re.sub(r"\bHAMILxxxii\s+TON\b", "HAMILTON", text)
        text = re.sub(r'\bexxxxvi\s+"?pression\b', "expression", text)
        text = re.sub(r'\bMADIlxxxiii\s+"?SON\b', "MADISON", text)
        text = re.sub(r"\bdis(?:c)?xxxiii\s+agreement\b", "disagreement", text)
        text = re.sub(
            r"\bbecxxxiv\s+(?:Essay\. Page\s+)?havior\b",
            "behavior",
            text,
        )

        # === CLEAN UP MULTIPLE BLANK LINES ===
        text = re.sub(r"\n{3,}", "\n\n", text)

        # === DEHYPHENATE LINE-LOCAL WRAPS ===
        # Exact seams above and attested spellings may cross a blank gap; the
        # two independently rejected layout collisions may not. Normalize
        # line-local quote furniture, then let the evidence-aware transform
        # decide the spelling.
        text = re.sub(r"(\w)- +\n", r"\1-\n", text)
        text = re.sub(r"(\w)-\n[ \t]+", r"\1-\n", text)
        # These ten residual wraps are independently supported by the Dawson/
        # Gutenberg transcription. Keep them exact and book-local: several are
        # OCR spellings, and a generic rule would also recreate known false joins.
        for wrapped, joined in _VERIFIED_RESIDUAL_WRAP_JOINS.items():
            text = text.replace(wrapped, joined)

        # === REFLOW PARAGRAPHS ===
        # Long quotations in this edition repeat an opening quote at the start of
        # every printed line. Reflow and quote-furniture removal must reach a
        # shared fixed point: joining an unquoted continuation can make two
        # quote-prefixed print lines newly adjacent.
        quoted_hyphen = re.compile(r'^("[^\n]*\w-\n)[ \t]*"([a-z])', re.MULTILINE)
        quoted_line = re.compile(r'^("[^\n]*)\n[ \t]*"([^\n]*)$', re.MULTILINE)
        # These two joins are independently verified and allow the fixed-point
        # quote cleanup to proceed even for isolated test excerpts.
        text = text.replace("erro-\nneous", "erroneous")
        text = text.replace("char-\nacter", "character")
        while True:
            updated = re.sub(r"([a-z,;:])\n([a-z])", r"\1 \2", text)
            # Period followed by lowercase = mid-sentence break, not a paragraph boundary
            updated = re.sub(r"([a-z]\.)\n([a-z])", r"\1 \2", updated)
            # Also handle cases ending with closing quote or parenthesis
            updated = re.sub(r"([a-z]['\")])\n([a-z])", r"\1 \2", updated)
            updated = quoted_hyphen.sub(r"\1\2", updated)
            updated = updated.replace("erro-\nneous", "erroneous")
            updated = updated.replace("char-\nacter", "character")
            updated = quoted_line.sub(r"\1 \2", updated)
            updated = _dehyphenate_federalist_page_gaps(updated)
            if updated == text:
                break
            text = updated

        text = text.replace("erro-\nneous", "erroneous")
        text = text.replace("char-\nacter", "character")

        return text
