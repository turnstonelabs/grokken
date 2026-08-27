"""Tests for transform functions."""

from grokken.transforms import encoding, ocr, structure, typography, whitespace


class TestEncoding:
    def test_normalize_to_utf8_windows_artifacts(self):
        text = "It\x92s a test\x97with dashes"
        result = encoding.normalize_to_utf8(text)
        assert result == "It's a test—with dashes"

    def test_strip_null_bytes(self):
        text = "Hello\x00World"
        assert encoding.strip_null_bytes(text) == "HelloWorld"

    def test_normalize_line_endings(self):
        text = "Line1\r\nLine2\rLine3\n"
        assert encoding.normalize_line_endings(text) == "Line1\nLine2\nLine3\n"


class TestOCR:
    def test_fix_common_errors(self):
        text = "tbe quick brown fox"
        assert ocr.fix_common_errors(text) == "the quick brown fox"

    def test_fix_long_s(self):
        text = "the firſt ſtep"
        assert ocr.fix_long_s(text) == "the first step"

    def test_fix_digit_letter_confusion(self):
        text = "the peop1e"
        assert ocr.fix_digit_letter_confusion(text) == "the people"


class TestTypography:
    def test_fix_ligatures(self):
        text = "ﬁnding the ﬂoor"
        assert typography.fix_ligatures(text) == "finding the floor"

    def test_normalize_quotes(self):
        text = "\u201cHello,\u201d she said, \u2018quietly\u2019"
        assert typography.normalize_quotes(text) == "\"Hello,\" she said, 'quietly'"

    def test_normalize_dashes(self):
        text = "word---word and word--word"
        result = typography.normalize_dashes(text)
        assert "—" in result  # em dash
        assert "–" in result  # en dash


class TestWhitespace:
    def test_dehyphenate(self):
        text = "prin-\nciples of psy-\nchology"
        result = whitespace.dehyphenate(text)
        assert result == "principles of psychology"

    def test_dehyphenate_does_not_cross_blank_lines(self):
        text = "prin-\n\nciples"

        assert whitespace.dehyphenate(text) == text
        assert whitespace.dehyphenate_aggressive(text) == text

    def test_dehyphenate_attested_joins_only_unambiguous_spelling(self):
        text = "These principles matter.\nOther prin-\nciples follow."

        assert whitespace.dehyphenate_attested(text) == (
            "These principles matter.\nOther principles follow."
        )

    def test_dehyphenate_attested_preserves_unattested_and_competing_forms(self):
        text = (
            "Keep this self-contained example.\n"
            "Do not make it self-\ncontained or join a novel-\nterm."
        )

        assert whitespace.dehyphenate_attested(text) == (
            "Keep this self-contained example.\n"
            "Do not make it self-contained or join a novel-\nterm."
        )

    def test_dehyphenate_attested_accepts_external_preservation_evidence(self):
        text = "The afterimage exists here, but this edition writes after-\nimage."

        assert whitespace.dehyphenate_attested(
            text,
            preserve_hyphenated=("after-image",),
        ) == ("The afterimage exists here, but this edition writes after-image.")

    def test_external_evidence_can_resolve_a_single_letter_fragment(self):
        text = "The source cites VII-\nx."

        assert (
            whitespace.dehyphenate_attested(
                text,
                preserve_hyphenated=("VII-x",),
            )
            == "The source cites VII-x."
        )

    def test_dehyphenate_attested_uses_strong_joined_form_frequency_dominance(self):
        text = (
            ("Pickwick " * 8)
            + "appears beside one Pick-wick variant.\n"
            + "The next Pick-\nwick occurrence follows the dominant spelling."
        )

        assert "next Pickwick occurrence" in whitespace.dehyphenate_attested(text)

    def test_dehyphenate_attested_keeps_hyphen_without_strong_dominance(self):
        text = (
            "One afterimage and another afterimage appear beside after-image.\n"
            "Keep this after-\nimage conservative."
        )

        assert "this after-image conservative" in whitespace.dehyphenate_attested(text)

    def test_dehyphenate_attested_preserves_formula_and_blank_line_boundaries(self):
        text = "Let xy be attested.\nThen x-\ny differs.\nKeep prin-\n\nciples apart."

        assert whitespace.dehyphenate_attested(text) == text

    def test_dehyphenate_attested_page_gaps_requires_independent_evidence(self):
        text = (
            "These principles recur; self-contained does too.\n"
            "Join prin-\n\nciples but preserve self-\n\ncontained and novel-\n\nterm."
        )

        assert whitespace.dehyphenate_attested_page_gaps(text) == (
            "These principles recur; self-contained does too.\n"
            "Join principles but preserve self-contained and novel-\n\nterm."
        )

    def test_dehyphenate_attested_can_reject_a_known_false_join(self):
        text = "A corrupt arcontained token exists, but leave ar-\n\ncontained unresolved."

        assert (
            whitespace.dehyphenate_attested_page_gaps(
                text,
                reject_joined=("arcontained",),
            )
            == text
        )

    def test_normalize_paragraphs(self):
        text = "Line one\nLine two\n\n\n\nNew paragraph"
        result = whitespace.normalize_paragraphs(text)
        assert "\n\n\n" not in result
        assert "\n\n" in result

    def test_trim(self):
        text = "  \n\nContent here\n\n  "
        assert whitespace.trim(text) == "Content here"


class TestStructure:
    def test_remove_page_headers(self):
        text = "CHAPTER ONE\n\nContent here\n\nCHAPTER ONE\n\nMore content"
        transform = structure.remove_page_headers(r"^CHAPTER ONE$")
        result = transform(text)
        assert "CHAPTER ONE" not in result
        assert "Content here" in result

    def test_remove_page_numbers(self):
        text = "Content\n\n— 42 —\n\nMore content\n\n[123]\n\nEnd"
        result = structure.remove_page_numbers(text)
        assert "42" not in result
        assert "123" not in result
        assert "Content" in result
