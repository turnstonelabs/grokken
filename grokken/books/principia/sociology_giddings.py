"""
Handler for "The Elements of Sociology" by Franklin Henry Giddings (1898).

A text-book for colleges and schools on sociological principles.

Score: 36.0
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_SAME_LINE_RUNNING_HEADS = (
    ("Formal Like-mindedness: Tradition and Conformity", r"\d{1,4}"),
    ("The Character and Efficiency of Organization", r"\d{1,4}"),
    ("The Composition and Unity of a Social Population", r"(?:31|33)"),
    ("The Social Mind: Modes of Like-mindedness", r"(?:123|125|127)"),
)
_CLIPPED_COLUMN_FOLIOS = frozenset(
    "255." if number == 255 else str(number)
    for number in range(237, 354, 2)
    if number not in {247, 269}
)
_PAGE_BREAK_WORD_JOINS = (
    ("dis", "appear"),
    ("immi", "grant"),
    ("ex", "periences"),
    ("re", "duced"),
    ("states", "men"),
    ("monarch", "ist"),
    ("tenden", "cies"),
    ("accomplish", "ment"),
    ("at", "tempts"),
    ("govern", "ments"),
    ("multiplica", "tion"),
    ("con", "trol"),
    ("com", "munity"),
)


def _normalized_line(line: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", line).casefold().split())


def _join_confirmed_page_break_words(text: str) -> str:
    for left, right in _PAGE_BREAK_WORD_JOINS:
        text = re.sub(
            rf"(?<!\p{{L}}){re.escape(left)}-\n\s*{re.escape(right)}(?!\p{{L}})",
            left + right,
            text,
        )
    return text


def _remove_same_line_running_heads(text: str) -> str:
    for header, folios in _SAME_LINE_RUNNING_HEADS:
        optional_period = r"\.?" if header.startswith("The Social Mind:") else ""
        text = re.sub(
            rf"(?m)^[ \t]*{re.escape(header)}{optional_period}[ \t]+{folios}"
            r"[ \t]*(?:\n|\Z)",
            "",
            text,
        )
    return text


def _remove_clipped_column_fragments(text: str) -> str:
    """Drop the short fragments in the 57 verified clipped-column page scans."""
    lines = text.splitlines()
    result: list[str] = []
    dropping = False
    for line in lines:
        stripped = line.strip()
        if stripped in _CLIPPED_COLUMN_FOLIOS:
            dropping = True
            continue
        if dropping:
            if not stripped:
                continue
            if len(stripped) < 40:
                continue
            dropping = False
        result.append(line)
    return "\n".join(result)


def _remove_recurrent_page_headers(text: str) -> str:
    """Remove recurrent short heads only in observed numbered page layouts."""
    lines = text.splitlines()
    normalized = [_normalized_line(line) for line in lines]
    counts = Counter(value for value in normalized if value)

    def is_header(index: int) -> bool:
        value = normalized[index]
        return (
            6 <= len(value) <= 100
            and counts[value] >= 3
            and any(character.isalpha() for character in value)
            and _FOLIO_LINE.fullmatch(lines[index]) is None
        )

    def adjacent_blocks(folio_index: int) -> list[list[int]]:
        before: list[int] = []
        index = folio_index - 1
        while index >= 0 and is_header(index) and len(before) < 2:
            before.insert(0, index)
            index -= 1
        after: list[int] = []
        index = folio_index + 1
        while index < len(lines) and is_header(index) and len(after) < 2:
            after.append(index)
            index += 1
        return [block for block in (before, after) if block]

    boundary_positions: dict[str, set[int]] = defaultdict(set)
    first_boundary: dict[str, int] = {}
    for folio_index, line in enumerate(lines):
        if _FOLIO_LINE.fullmatch(line) is None:
            continue
        for block in adjacent_blocks(folio_index):
            block_start = min(folio_index, block[0])
            if block_start == 0 or lines[block_start - 1].strip():
                continue
            for header_index in block:
                value = normalized[header_index]
                boundary_positions[value].add(header_index)
                first_boundary[value] = min(first_boundary.get(value, header_index), header_index)

    dropped: set[int] = set()
    for folio_index, line in enumerate(lines):
        if folio_index in dropped or _FOLIO_LINE.fullmatch(line) is None:
            continue
        eligible: list[tuple[bool, int, list[int]]] = []
        for block in adjacent_blocks(folio_index):
            if any(index in dropped for index in block):
                continue
            block_start = min(folio_index, block[0])
            has_blank_boundary = block_start > 0 and not lines[block_start - 1].strip()
            established_layout = any(
                len(boundary_positions[normalized[index]]) >= 2
                and folio_index >= first_boundary[normalized[index]]
                for index in block
            )
            if has_blank_boundary or established_layout:
                evidence = sum(len(boundary_positions[normalized[index]]) for index in block)
                eligible.append((has_blank_boundary, evidence, block))
        if not eligible:
            continue
        _, _, block = max(eligible, key=lambda item: (item[0], item[1], len(item[2])))
        dropped.update((folio_index, *block))

    return "\n".join(line for index, line in enumerate(lines) if index not in dropped)


class SociologyGiddings(BookProcessor):
    """
    Processor for The Elements of Sociology.
    """

    barcode = "TZ1HCP"
    title = "The Elements of Sociology: a text-book for colleges and schools"
    author = "Giddings, Franklin Henry"
    date = "1898"

    notes = """
    Sociology textbook for educational use.

    Known quirks:
    - Academic sociology content
    - Discussion of family structures, tribes
    - References to Greenland, Brazil, various cultures
    - Sociological terminology (polyandrian, savagery)
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for The Elements of Sociology."""
        text = _remove_clipped_column_fragments(text)
        text = _remove_same_line_running_heads(text)
        text = _remove_recurrent_page_headers(text)
        text = _join_confirmed_page_break_words(text)
        text = re.sub(r"\bIl success\b", "Ill success", text)
        text = text.replace("de-`\nvelopment", "development")
        text = re.sub(r"(?m)^[ \t]*✔[ \t]*(?:\n|\Z)", "", text)
        return re.sub(r"\n{3,}", "\n\n", text)
