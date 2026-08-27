"""
Handler for William James's "The Principles of Psychology" (1890).

This is the top-scoring book in The Principia 34 (score: 39.0).
A foundational work in psychology, known for its comprehensive
treatment of consciousness, habit, emotion, and the self.

Two volumes, ~400K tokens.
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_PRESERVE_HYPHENATED = frozenset(
    {
        "after-effects",
        "after-image",
        "after-images",
        "after-mark",
        "anaemia-business",
        "anti-sensationalist",
        "apperception-product",
        "atoms-producing",
        "avant-courier",
        "back-door",
        "bas-relief",
        "brain-centre",
        "brain-lesion",
        "brain-paths",
        "brain-power",
        "brain-seat",
        "brain-tract",
        "breakfast-table",
        "breast-bone",
        "breath-holding",
        "by-gone",
        "can-be",
        "candle-flame",
        "car-window",
        "cerebro-mental",
        "clementi-rightness",
        "co-operative",
        "color-contrast",
        "consciousness-elements",
        "contrast-colors",
        "drainage-channel",
        "drainage-channels",
        "dreary-feeling",
        "dress-parade",
        "earth-born",
        "eighteenth-century",
        "elbow-joint",
        "epoch-making",
        "experience-hypothesis",
        "experience-theory",
        "eye-movements",
        "finger-tip",
        "finger-tips",
        "first-comers",
        "fish-basket",
        "fore-effect",
        "four-cornered",
        "good-sized",
        "goose-flesh",
        "ground-tone",
        "guinea-pig",
        "half-dollar",
        "heart-beat",
        "horizon-line",
        "hunger-pangs",
        "hunting-instinct",
        "identity-theory",
        "ideo-motor",
        "india-rubber",
        "infinitely-repeated",
        "joint-feeling",
        "last-named",
        "lately-finished",
        "left-hand",
        "local-signs",
        "long-treasured",
        "medium-sized",
        "memory-image",
        "mind-reading",
        "mouth-cavity",
        "movement-feeling",
        "much-used",
        "nerve-centres",
        "nerve-current",
        "nerve-currents",
        "nerve-process",
        "nerve-tracts",
        "nerve-trunk",
        "never-failing",
        "ninety-nine",
        "non-attention",
        "non-ego",
        "non-existent",
        "non-similar",
        "non-spatial",
        "number-series",
        "object-emotionally",
        "oil-cloth",
        "one-fluid",
        "pen-holder",
        "pen-point",
        "pencil-point",
        "pendulum-bob",
        "pitch-plaster",
        "pleasure-theory",
        "pocket-corkscrew",
        "post-hypnotic",
        "pre-existence",
        "pre-exists",
        "pseudo-hallucinations",
        "pseudo-hallucinatory",
        "quick-witted",
        "ready-made",
        "research-societies",
        "self-command",
        "self-evident",
        "self-mobility",
        "sense-data",
        "sense-impression",
        "sense-organ",
        "sense-organs",
        "sense-spaces",
        "she-bear",
        "sign-using",
        "skin-feelings",
        "skin-spaces",
        "so-called",
        "space-determinations",
        "space-element",
        "space-experiences",
        "space-import",
        "space-order",
        "space-perception",
        "space-percepts",
        "space-sensation",
        "space-theories",
        "space-world",
        "splitting-off",
        "stove-pipe",
        "sub-universe",
        "sword-hilt",
        "table-cloth",
        "terror-paralysis",
        "their-mutual",
        "thought-processes",
        "time-orders",
        "to-day",
        "tobacco-smoke",
        "trance-like",
        "trance-subject",
        "vapor-density",
        "vii-x",
        "volume-units",
        "wall-papers",
        "well-marked",
        "wide-spread",
    }
)


def _dehyphenate_psychology(text: str) -> str:
    """Use same-book and Project Gutenberg #57634 spelling evidence."""
    return whitespace.dehyphenate_attested(
        text,
        preserve_hyphenated=_PRESERVE_HYPHENATED,
    )


class PrinciplesPsychology(BookProcessor):
    """
    Processor for William James's Principles of Psychology.
    """

    barcode = "32044010149714"
    title = "The Principles of Psychology"
    author = "James, William"
    date = "1890"

    notes = """
    Two-volume work, considered foundational in psychology.

    Known quirks:
    - Headers alternate between chapter title and "PRINCIPLES OF PSYCHOLOGY"
    - Footnotes use superscript numbers
    - Contains occasional Greek passages (untransliterated)
    - Some figures/diagrams referenced but not present in OCR

    The OCR quality is generally good (high OCR score contributed to
    its top ranking).
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
        # Whitespace
        _dehyphenate_psychology,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """
        Book-specific cleanup for Principles of Psychology.

        1. Removes front matter (library stamps, title page, table of contents)
        2. Removes back matter (index, advertisements, library stamps)
        3. Removes running headers throughout the book
        """
        import regex as re

        # === STRIP FRONT MATTER ===
        # Front matter includes: library stamps, title page, copyright, table of contents
        # Actual content starts with "PSYCHOLOGY.\nCHAPTER XVII."
        front_marker = "PSYCHOLOGY.\nCHAPTER XVII."
        front_pos = text.find(front_marker)
        if front_pos > 0:
            # Keep from "CHAPTER XVII." onwards
            text = text[front_pos + len("PSYCHOLOGY.\n") :]

        # === STRIP BACK MATTER ===
        # Book ends with "THE END." followed by index, ads, library stamps
        end_match = re.search(r"THE END\.\s*\n", text)
        if end_match:
            text = text[: end_match.end()]

        # === BOOK-SPECIFIC OCR FIXES ===

        # Roman numerals decoded as visually similar Cyrillic letters. Keep the
        # replacements context-specific because diagrams also use letter labels.
        text = text.replace("Vol. п.", "Vol. II.")
        text = text.replace("vol. ш.", "vol. III.")
        text = text.replace("Seele, п (", "Seele, II (")
        text = text.replace("Wille, пI.", "Wille, II.")
        text = text.replace("Mind, ш.", "Mind, III.")
        text = text.replace("(Psychology, г.", "(Psychology, I.")
        text = text.replace("Centralblatt, п.", "Centralblatt, II.")

        # Homoglyph repairs limited to their verified scan contexts: three
        # standalone figure labels and one proverb. Preserve other lookalikes.
        text = re.sub(r"^[ \t]*с[ \t]*$", "c", text, flags=re.MULTILINE)
        text = text.replace('" а bird in the hand', '" a bird in the hand')
        text = text.replace("favμa", "θαῦμα")

        # Exact non-prose fragments confirmed in the scan's figure/page contexts.
        # Keep this allowlist narrow: the book contains real Greek, and several
        # isolated lookalikes are potentially meaningful diagram labels.
        scan_noise_lines = ("肇", "ՂԱՏ.", "Им", "ん", "мли", "И", "Л", "п", "ि", "་")
        scan_noise = "|".join(re.escape(fragment) for fragment in scan_noise_lines)
        text = re.sub(
            rf"^[ \t]*(?:{scan_noise})[ \t]*$\n?",
            "",
            text,
            flags=re.MULTILINE,
        )

        # === REMOVE RUNNING HEADERS ===

        # Pattern 1: Page number on own line, followed by "PSYCHOLOGY." (or OCR variants)
        # Matches: "\n322\nPSYCHOLOGY.\n" or "\n322\nPSYCHOLOG Y.\n" (OCR error with space)
        text = re.sub(
            r"\n\d{1,4}\nPSYCHOLOG\s?Y\.\n",
            "\n",
            text,
        )

        # Pattern 2: Page number on own line, followed by other all-caps headers
        # (chapter titles like "SENSATION.", "IMAGINATION.", "INDEX.", etc.)
        # Note: Use [ ] (space only) not [\s] to avoid matching newlines
        text = re.sub(
            r"\n\d{1,4}\n([A-Z][A-Z ]{2,50}\.)\n",
            "\n",
            text,
        )

        # Pattern 3: All-caps header on own line, followed by page number on next line
        # Matches: "SENSATION.\n3\n" or "NECESSARY TRUTHS-EFFECTS OF EXPERIENCE.\n689\n"
        # Note: Use [ -] (space and hyphen) not [\s-] to avoid matching newlines
        text = re.sub(
            r"\n([A-Z][A-Z -]{2,50}\.)\n\d{1,4}\n",
            "\n",
            text,
        )

        # Pattern 4: Page number followed by header on same line (original patterns)
        # Note: Use [ ] (space only) not [\s] to avoid matching newlines
        text = re.sub(
            r"^[ \t]*\d+[ \t]+(PRINCIPLES OF PSYCHOLOGY|[A-Z][A-Z ]+)[ \t]*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Pattern 5: Chapter title followed by page number on same line
        # Includes hyphens for titles like "NECESSARY TRUTHS-EFFECTS OF EXPERIENCE."
        # Note: Use [ -] (space and hyphen) not [\s-] to avoid matching newlines
        text = re.sub(
            r"^([A-Z][A-Z -]+\.?)[ \t]+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # The scan sometimes inserts a blank line between a page number and a
        # known running header. Remove only those evidenced pairs; standalone
        # numbers also occur as meaningful labels in the many diagrams.
        residual_header = (
            r"(?:PSYCHOLOG\s?Y\.?|THE PERCEPTION OF THINGS|"
            r"THE PERCEPTION OF,? SPACE\.|INSTINCT\.?)"
        )
        text = re.sub(
            rf"^[ \t]*\d{{1,4}}[ \t]*$\n(?:[ \t]*\n)?"
            rf"[ \t]*{residual_header}[ \t]*$\n?",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            rf"^[ \t]*{residual_header}[ \t]*$\n(?:[ \t]*\n)?"
            rf"[ \t]*\d{{1,4}}[ \t]*$\n?",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Residual variants in this scan: missing punctuation, an inserted comma,
        # and one cropped fragment of "PSYCHOLOGY". The actual chapter title is
        # "THE PERCEPTION OF SPACE.*", so the unstarred forms are running headers.
        text = re.sub(
            r"^[ \t]*(?:PSYCHOLOG\s?Y\.?|THE PERCEPTION OF THINGS|"
            r"THE PERCEPTION OF,? SPACE\.|CHOL)[ \t]*$\n?",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Repeated chapter-name headers whose following text makes their running-
        # header role unambiguous. Preserve the real chapter headings above them.
        text = re.sub(
            r"^[ \t]*(?:SENSATION\.(?=\none new simple)|"
            r"INSTINCT\.?(?=\n(?:\d{1,4}\n)?(?:either run|Let us now test))|"
            r"WILL\.(?=\nTurning now))[ \t]*\n?",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Clean up any resulting multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Page-furniture removal exposes additional line-break candidates. Join
        # only independently attested spellings; ambiguous compounds and layout
        # seams retain their source hyphen for explicit review.
        text = whitespace.dehyphenate_attested_page_gaps(
            text,
            preserve_hyphenated=_PRESERVE_HYPHENATED,
        )

        # These three historical-ligature spellings are verified against the
        # independent transcription but occur only in split form in this scan.
        for source, target in (
            ("hemian-\næsthetics", "hemianæsthetics"),
            ("an-\næsthetic", "anæsthetic"),
            ("an-\næsthesia", "anæsthesia"),
        ):
            text = text.replace(source, target)

        # === REFLOW PARAGRAPHS ===
        # Join lines that are mid-paragraph (OCR line breaks within sentences)
        # Pattern: lowercase letter at end of line, newline, lowercase letter at start
        # Replace with: lowercase, space, lowercase (joining the lines)
        text = re.sub(r"([a-zæœ,;:])\n([a-zæœ])", r"\1 \2", text)

        # Also handle cases ending with closing quote or parenthesis
        text = re.sub(r"([a-zæœ]['\")])\n([a-zæœ])", r"\1 \2", text)

        # One-off defects confirmed against an independent transcription of the
        # same volume. These are deliberately exact so similarly shaped text and
        # intentional paragraph boundaries remain untouched.
        verified_repairs = (
            ("Erkenntnisstheoric", "Erkenntnisstheorie"),
            ("(P. 266.)\n6\nThe commonplace", "(P. 266.)\n\nThe commonplace"),
            (
                "that of predicate\n1\n1\n1\n1\n\nto subject",
                "that of predicate to subject",
            ),
            ("turn to consider.\n6\nPugnacity", "turn to consider.\n\nPugnacity"),
            ("p. 593.\n4\n\nonly thing", "p. 593.\n\nonly thing"),
            ("own.. Every visual", "own. Every visual"),
            ("colored light. This\nThis may be done", "colored light. This may be done"),
            ("facewith", "face with"),
            ("\ndinary parlance hallucination", "\nIn ordinary parlance hallucination"),
            ("patho logical", "pathological"),
            ("\nthen, if the pain seem", "\nWhat wonder, then, if the pain seem"),
            ("Bd. xvII.", "Bd. xvii."),
            ("spacedeterminations", "space-determinations"),
            ("associa tion", "association"),
            ("I ca find", "I can find"),
            ("\nguage is assuredly", "\nlanguage is assuredly"),
            ("associa–\ntion by similarity", "association by similarity"),
            ("negi ativeness", "negativeness"),
            ("pleasure\n\nof its own", "pleasure of its own"),
            ("\nstudent, a friend of my own", "\nAnother student, a friend of my own"),
            ("\ncoup that we find", "\naprès coup that we find"),
            ("\nof them have no single sensation", "\nLet some of them have no single sensation"),
            ("and the mechanical\n\nphilosophy is only", "and the mechanical philosophy is only"),
        )
        for corrupted, repaired in verified_repairs:
            text = text.replace(corrupted, repaired)

        return text
