"""
Handler for "Principles of Political Economy" by John Stuart Mill (1884 edition).

Mill's foundational work on economics, first published in 1848.
This is the 1884 edition.

Score: 38.0
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_SAME_LINE_RUNNING_HEADS = (
    "INFLUENCE OF CURRENCY ON FOREIGN TRADE.",
    "COMPETITION OF COUNTRIES IN THE SAME MARKET.",
    "INFLUENCE OF INDUSTRIAL PROGRESS ON PRICES.",
    "INFLUENCE OF PROGRESS ON RENTS, PROFITS, ETC.",
    "PROBABLE FUTURE OF THE LABOURING CLASSES.",
)
_QUIRE_FOOTER = re.compile(r"(?m)^[ \t]*VOL\.[ \t]*II\.?[ \t]*[-–—][ \t]*-?\d{1,3}[ \t]*(?:\n|\Z)")
_BOOK_CHAPTER_RUNNING_HEAD = re.compile(
    r"^[ \t]*BOOK[ \t]+(?:[IVXLC]+|1)[.,]?[ \t]+CHAPTER[ \t]+"
    r"(?:[IVXLC]+|\d+)[.,]?[ \t]*(?:-?[ \t]*[§$*][ \t]*\d*\.?)?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
_SECTION_FRAGMENT_LINE = re.compile(r"^[ \t]*-?[ \t]*[§$*][ \t]*\d*\.?[ \t]*$")
_EXACT_RUNNING_HEAD_BLOCKS = tuple(
    tuple(block.split("\n"))
    for block in (
        "10\nINFLUENCE OF PROGRESS ON RENTS, PROFITS, ETC.",
        "PROBABLE FUTURE OF THE LABOURING CLASSES.\n357",
        "PROBABLE FUTURE OF THE LAROURING CLASSES.\n377",
        "428\nBOOK V. 梦\nCHAPTER III. § 5.",
        "DIRECT AND INDIRECT TAXES COMPARED..\n473",
        "USURY LAWS.\n541",
        "USURY LAWS.\n543",
        "REGULATION OF THE PRICE OF FOOD.\n545",
        "MONOPOLIES.\n547",
    )
)
_PAGE_BREAK_WORD_JOINS = (
    ("pro", "duction"),
    ("indus", "trious"),
    ("ad", "ditional"),
    ("de", "mand"),
    ("ordi", "nary"),
    ("lend", "ing"),
    ("What", "ever"),
    ("eco", "nomical"),
    ("how", "ever"),
    ("im", "poverishing"),
    ("unavoid", "able"),
    ("advan", "tage"),
    ("her", "self"),
    ("fana", "ticism"),
    ("regard", "ed"),
    ("attain", "ing"),
    ("incum", "bent"),
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


class PoliticalEconomyMill1884(BookProcessor):
    """
    Processor for Principles of Political Economy (Mill, 1884).
    """

    barcode = "LI3QQB"
    title = "Principles of Political Economy"
    author = "Mill, John Stuart"
    date = "1884"

    notes = """
    Mill's classic work on political economy.

    Known quirks:
    - Running headers with Book/Chapter markers (BOOK IV. CHAPTER IV. §3.)
    - Economic theory and philosophy
    - Dense argumentative prose
    - Footnotes with references
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
        """Book-specific cleanup for Principles of Political Economy (Mill)."""
        text = _remove_exact_page_furniture(text)
        text = _remove_recurrent_page_headers(text)
        text = _join_confirmed_page_break_words(text)
        return re.sub(r"\n{3,}", "\n\n", text)
