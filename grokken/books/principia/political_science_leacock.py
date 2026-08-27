"""
Handler for "Elements of Political Science" by Stephen Leacock (1906).

A textbook on political science covering government structures, constitutional law,
and comparative politics.

Score: 38.0
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_LEADING_FOLIO_RUNNING_HEAD = re.compile(
    r"(?m)^[ \t]*\d{1,4}[ \t]+THE STRUCTURE OF THE GOVERNMENT`?[ \t]*(?:\n|\Z)"
)
_TRAILING_FOLIO_RUNNING_HEADS = (
    "THE JUDICIARY AND THE ELECTORATE",
    "RELATION OF STATES TO ONE ANOTHER",
)
_PAGE_BREAK_WORD_JOINS = (
    ("be", "ginning"),
    ("author", "ity"),
    ("supe", "riority"),
    ("identi", "fication"),
    ("politi", "cal"),
    ("exist", "ing"),
    ("regu", "lating"),
    ("con", "stitutional"),
    ("sim", "plicity"),
    ("clos", "ing"),
    ("gov", "ernment"),
    ("constitu", "tion"),
    ("differ", "ent"),
    ("depart", "mental"),
    ("prin", "ciple"),
    ("Al", "though"),
    ("ad", "mitted"),
    ("compo", "nent"),
    ("ad", "dition"),
    ("Con", "stitution"),
    ("or", "ganized"),
    ("pre", "cedence"),
    ("indi", "vidualistic"),
    ("sur", "plus"),
    ("unre", "stricted"),
    ("appli", "cation"),
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


def _remove_exact_page_furniture(text: str) -> str:
    text = _LEADING_FOLIO_RUNNING_HEAD.sub("", text)
    for header in _TRAILING_FOLIO_RUNNING_HEADS:
        text = re.sub(
            rf"(?m)^[ \t]*{re.escape(header)}[ \t]+\d{{1,4}}[ \t]*(?:\n|\Z)",
            "",
            text,
        )
    return text


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


class PoliticalScience(BookProcessor):
    """
    Processor for Elements of Political Science.
    """

    barcode = "32044097049340"
    title = "Elements of Political Science"
    author = "Leacock, Stephen"
    date = "1906"

    notes = """
    Political science textbook by Stephen Leacock (also known as a humorist).

    Known quirks:
    - Many numbered lists (ministers, departments)
    - Comparative government structure tables
    - Chapter/section organization
    - Clean academic prose
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
        """Book-specific cleanup for Elements of Political Science."""
        text = _remove_exact_page_furniture(text)
        text = _remove_recurrent_page_headers(text)
        text = _join_confirmed_page_break_words(text)
        text = text.replace(
            "with a view to discov-\n\nmay\nering the teaching of experience",
            "with a view to discovering the teaching of experience",
        )
        text = text.replace("Ghe Riverside Press", "The Riverside Press")
        text = text.replace("says\nsays the\nsame authority", "says the\nsame authority")
        text = re.sub(r"(?m)^[ \t]*(?:99 66|wwwwwwwwww|✓)[ \t]*(?:\n|\Z)", "", text)
        text = text.replace("medi-\næval", "mediæval")
        return re.sub(r"\n{3,}", "\n\n", text)
