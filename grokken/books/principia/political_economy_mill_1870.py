"""
Handler for "Principles of Political Economy" by John Stuart Mill (1870 edition).

An alternate edition of Mill's foundational work on economics.

Score: 37.9
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_SAME_LINE_RUNNING_HEADS = (
    "PRODUCTION ON A LARGE AND ON A SMALL SCALE.",
    "LAW OF INCREASE OF PRODUCTION FROM LAND.",
)
_QUIRE_FOOTER = re.compile(
    r"(?m)^[ \t]*VOL\.[ \t]*(?:I|1)\.?[ \t]*[-–—][ \t]*-?\d{1,3}[ \t]*(?:\n|\Z)"
)
_BOOK_CHAPTER_RUNNING_HEAD = re.compile(
    r"^[ \t]*BOOK[ \t]+(?:[IVXLC]+|1)[.,]?[ \t]+CHAPTER[ \t]+"
    r"(?:[IVXLC]+|\d+)[.,]?[ \t]*(?:-?[ \t]*[§$*][ \t]*\d*\.?)?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
_SECTION_FRAGMENT_LINE = re.compile(r"^[ \t]*-?[ \t]*[§$*][ \t]*\d*\.?[ \t]*$")
_EXACT_RUNNING_HEAD_BLOCKS = tuple(
    tuple(block.split("\n"))
    for block in (
        "92\nI. CHAPTER IV. § 3.\n1",
        "PRODUCTION ON A LARGE AND ON A SMALL SCALE.\n191",
        "PRODUCTION ON A LARGE AND ON A SMALL SCALE.\n193",
        "LAW OF THE INCREASE OF CAPITAL\n221",
        "ST. SIMONISM.\n273",
        "FOURIERISM.\n275",
        "FOURIERISM.\n277",
        "BEQUEST.\n287",
        "BEQUEST.\n289",
        "CLASSES WHO DIVIDE THE PRODUCE.\n303",
        "CLASSES WHO DIVIDE THE PRODUCE.\n305",
    )
)
_PAGE_BREAK_WORD_JOINS = (
    ("pre", "vailed"),
    ("subse", "quent"),
    ("indus", "try"),
    ("effect", "ed"),
    ("car", "riage"),
    ("deterio", "rated"),
    ("period", "ically"),
    ("as", "sented"),
    ("pur", "chasers"),
    ("pro", "duction"),
    ("econ", "omy"),
    ("pos", "sible"),
    ("occa", "sioned"),
    ("incontesta", "ble"),
    ("fore", "thought"),
    ("har", "vests"),
    ("Amer", "ican"),
    ("associa", "tion"),
    ("cor", "rection"),
    ("every", "body"),
    ("improve", "ment"),
    ("popula", "tion"),
    ("some", "thing"),
    ("circum", "stances"),
    ("it", "self"),
    ("tem", "porarily"),
    ("be", "lieve"),
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
    text = _QUIRE_FOOTER.sub("", text)
    lines = text.splitlines()
    dropped: set[int] = set()
    for index, line in enumerate(lines):
        if _BOOK_CHAPTER_RUNNING_HEAD.fullmatch(line) is None:
            continue
        dropped.add(index)
        for direction in (-1, 1):
            adjacent = index + direction
            while 0 <= adjacent < len(lines) and (
                _FOLIO_LINE.fullmatch(lines[adjacent])
                or _SECTION_FRAGMENT_LINE.fullmatch(lines[adjacent])
            ):
                dropped.add(adjacent)
                adjacent += direction
    text = "\n".join(line for index, line in enumerate(lines) if index not in dropped)
    for header in _SAME_LINE_RUNNING_HEADS:
        text = re.sub(
            rf"(?m)^[ \t]*{re.escape(header)}[ \t]+\d{{1,3}}[ \t]*(?:\n|\Z)",
            "",
            text,
        )
    lines = text.splitlines()
    dropped = set()
    for block in _EXACT_RUNNING_HEAD_BLOCKS:
        width = len(block)
        for start in range(len(lines) - width + 1):
            if tuple(lines[start : start + width]) == block:
                dropped.update(range(start, start + width))
    text = "\n".join(line for index, line in enumerate(lines) if index not in dropped)
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


class PoliticalEconomyMill1870(BookProcessor):
    """
    Processor for Principles of Political Economy (Mill, 1870).
    """

    barcode = "HXQ9SJ"
    title = "Principles of Political Economy, with some of their applications to social philosophy"
    author = "Mill, John Stuart"
    date = "1870"

    notes = """
    Earlier edition of Mill's political economy work.

    Known quirks:
    - Similar to 1884 edition
    - Running headers with Book/Chapter markers
    - Economic theory and philosophy
    - Dense argumentative prose
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
        """Book-specific cleanup for Principles of Political Economy (Mill 1870)."""
        text = _remove_exact_page_furniture(text)
        text = _remove_recurrent_page_headers(text)
        text = _join_confirmed_page_break_words(text)
        return re.sub(r"\n{3,}", "\n\n", text)
