"""
Whitespace and line-handling transforms.

Handles paragraph breaks, line wrapping, hyphenation,
and other whitespace-related issues.
"""

import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable

import regex as re

# Precompiled patterns for dehyphenate. Horizontal whitespace is deliberate:
# ``\s*`` also consumes blank lines and can join across page furniture.
_RE_DEHYPHENATE = re.compile(r"(\w+)-\n[ \t]*([a-z])")

# Conservative, evidence-backed dehyphenation for quality-sensitive corpora.
_RE_DEHYPHENATE_ATTESTED = re.compile(
    r"(?P<left>\p{L}[\p{L}\p{M}]*)-\n[ \t]*(?P<right>[a-z][\p{L}\p{M}]*)"
)
_RE_DEHYPHENATE_ATTESTED_PAGE_GAP = re.compile(
    r"(?P<left>\p{L}[\p{L}\p{M}]*)-\n(?:[ \t]*\n)?[ \t]*"
    r"(?P<right>\p{Ll}[\p{L}\p{M}]*)"
)
_RE_WORD = re.compile(r"(?<![\p{L}\p{M}\p{N}_])[\p{L}\p{M}]+(?![\p{L}\p{M}\p{N}_])")
_RE_INLINE_HYPHENATED_WORD = re.compile(
    r"(?<![\p{L}\p{M}\p{N}_])(?P<left>\p{L}[\p{L}\p{M}]*)-"
    r"(?P<right>[a-z][\p{L}\p{M}]*)(?![\p{L}\p{M}\p{N}_])"
)
_ATTESTATION_DOMINANCE_RATIO = 8

# Precompiled patterns for dehyphenate_aggressive
_RE_DEHYPHENATE_AGG = re.compile(r"(\w+)-[ \t]*\n[ \t]*([a-z])")

# Precompiled patterns for normalize_paragraphs
_RE_EXCESS_NEWLINES = re.compile(r"\n{3,}")
_RE_SINGLE_NEWLINE = re.compile(r"(?<=[^\n])\n(?=[^\n])")

# Precompiled patterns for normalize_whitespace
_RE_MULTI_SPACE = re.compile(r" +")
_RE_TRAILING_SPACE = re.compile(r" +$", re.MULTILINE)

# Precompiled pattern for strip_blank_lines
_RE_BLANK_LINE = re.compile(r"^\s*$\n", re.MULTILINE)


def dehyphenate(text: str) -> str:
    """
    Rejoin words split across lines by hyphenation.

    "prin-\\nciples" -> "principles"

    Only joins when the hyphen is at end of line followed by
    lowercase continuation, to avoid breaking intentional hyphens.
    """
    # Hyphen at end of line followed by lowercase letter
    text = _RE_DEHYPHENATE.sub(r"\1\2", text)
    return text


def _canonical_word(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().replace("æ", "ae").replace("œ", "oe")


def _dehyphenate_attested(
    text: str,
    pattern: re.Pattern[str],
    *,
    preserve_hyphenated: Iterable[str] = (),
    reject_joined: Iterable[str] = (),
) -> str:
    word_counts = Counter(_canonical_word(match.group(0)) for match in _RE_WORD.finditer(text))
    hyphenated_counts = Counter(
        _canonical_word(f"{match.group('left')}-{match.group('right')}")
        for match in _RE_INLINE_HYPHENATED_WORD.finditer(text)
    )
    externally_preserved = {_canonical_word(value) for value in preserve_hyphenated}
    rejected_joined = {_canonical_word(value) for value in reject_joined}

    def replace_if_attested(match: re.Match[str]) -> str:
        left = match.group("left")
        right = match.group("right")
        joined = left + right
        hyphenated = f"{left}-{right}"
        canonical_joined = _canonical_word(joined)
        canonical_hyphenated = _canonical_word(hyphenated)
        if canonical_joined in rejected_joined:
            return match.group(0)
        # Explicit book-local evidence is strong enough to resolve even the
        # single-letter fragments that the generic math guard must preserve.
        if canonical_hyphenated in externally_preserved:
            return hyphenated
        # Single-letter fragments are commonly variables or operators in
        # mathematical/scientific layouts; book-local evidence must resolve them.
        if len(left) < 2 or len(right) < 2:
            return match.group(0)
        joined_count = word_counts[canonical_joined]
        hyphenated_count = hyphenated_counts[canonical_hyphenated]
        if joined_count and (
            not hyphenated_count or joined_count >= _ATTESTATION_DOMINANCE_RATIO * hyphenated_count
        ):
            return joined
        if hyphenated_count:
            return hyphenated
        return match.group(0)

    return pattern.sub(replace_if_attested, text)


def dehyphenate_attested(
    text: str,
    *,
    preserve_hyphenated: Iterable[str] = (),
    reject_joined: Iterable[str] = (),
) -> str:
    """Rejoin only line-break words independently attested in the same text.

    A candidate such as ``prin-\nciples`` is joined when ``principles`` occurs
    elsewhere as a whole word. If ``prin-ciples`` is attested instead, the line
    wrap is removed while its lexical hyphen is retained. When both forms occur,
    only strong joined-form frequency dominance overrides the hyphenated form;
    external preservation evidence remains authoritative. Ambiguous, unattested,
    numeric, and formula cases remain unchanged for book-local review. The
    transform never crosses a blank line.
    """
    return _dehyphenate_attested(
        text,
        _RE_DEHYPHENATE_ATTESTED,
        preserve_hyphenated=preserve_hyphenated,
        reject_joined=reject_joined,
    )


def dehyphenate_attested_page_gaps(
    text: str,
    *,
    preserve_hyphenated: Iterable[str] = (),
    reject_joined: Iterable[str] = (),
) -> str:
    """Evidence-backed dehyphenation across at most one removed-page blank line.

    This is for book-local post-processing after verified page furniture has
    been removed. It applies the same independent-attestation rule as
    :func:`dehyphenate_attested` but also recognizes Unicode lowercase starts.
    """
    return _dehyphenate_attested(
        text,
        _RE_DEHYPHENATE_ATTESTED_PAGE_GAP,
        preserve_hyphenated=preserve_hyphenated,
        reject_joined=reject_joined,
    )


def dehyphenate_aggressive(text: str) -> str:
    """
    More aggressive dehyphenation.

    Also handles cases where there might be spaces after the hyphen
    or before the continuation.
    """
    # Handles hyphens with optional whitespace before/after newline
    text = _RE_DEHYPHENATE_AGG.sub(r"\1\2", text)

    return text


def normalize_paragraphs(text: str) -> str:
    """
    Normalize paragraph breaks.

    - Collapse 3+ newlines to double newline (paragraph break)
    - Single newlines within paragraphs become spaces
    """
    # Collapse excessive newlines
    text = _RE_EXCESS_NEWLINES.sub("\n\n", text)

    # Single newlines -> space (but preserve paragraph breaks)
    # This joins lines within a paragraph
    text = _RE_SINGLE_NEWLINE.sub(" ", text)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace.

    - Tabs to spaces
    - Multiple spaces to single space
    - Trim trailing whitespace from lines
    """
    # Tabs to spaces
    text = text.replace("\t", " ")

    # Multiple spaces to single
    text = _RE_MULTI_SPACE.sub(" ", text)

    # Trailing whitespace
    text = _RE_TRAILING_SPACE.sub("", text)

    # Leading whitespace (optional - might want to preserve indentation)
    # text = re.sub(r"^ +", "", text, flags=re.MULTILINE)

    return text


def strip_blank_lines(text: str) -> str:
    """Remove completely blank lines."""
    return _RE_BLANK_LINE.sub("", text)


def collapse_blank_lines(max_consecutive: int = 2) -> Callable[[str], str]:
    """
    Factory: returns a transform that collapses consecutive blank lines.

    Args:
        max_consecutive: Maximum number of consecutive blank lines to keep.

    Returns:
        Transform function that collapses blank lines.

    Example:
        collapse_blank_lines(max_consecutive=2)
    """
    if max_consecutive < 1:
        raise ValueError(f"max_consecutive must be >= 1, got {max_consecutive}")

    compiled = re.compile(r"(\n\s*){" + str(max_consecutive + 1) + r",}")
    replacement = "\n" * max_consecutive

    def transform(text: str) -> str:
        return compiled.sub(replacement, text)

    transform.__doc__ = f"Collapse blank lines to max {max_consecutive} consecutive"
    return transform


def trim(text: str) -> str:
    """Strip leading and trailing whitespace from entire text."""
    return text.strip()


def unwrap_lines(text: str, min_line_length: int = 60) -> str:
    """
    Unwrap hard-wrapped lines into paragraphs.

    Useful for OCR'd text where each line of the original page
    became a separate line, but paragraphs should flow.

    Args:
        text: Input text with hard line wraps.
        min_line_length: Lines shorter than this at paragraph end
                        are considered paragraph breaks.

    Returns:
        Text with lines unwrapped into paragraphs.
    """
    lines = text.split("\n")
    paragraphs = []
    current_para = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Empty line = paragraph break
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
        elif len(stripped) < min_line_length and not stripped.endswith("-"):
            # Short line not ending in hyphen = end of paragraph
            current_para.append(stripped)
            paragraphs.append(" ".join(current_para))
            current_para = []
        else:
            current_para.append(stripped)

    # Don't forget the last paragraph
    if current_para:
        paragraphs.append(" ".join(current_para))

    return "\n\n".join(paragraphs)
