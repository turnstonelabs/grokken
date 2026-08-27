"""
Handler for "The Writings of Harriet Beecher Stowe" (1896 Riverside Edition).

Volume XIII of a sixteen-volume collection with biographical introductions,
portraits, and other illustrations.

Score: 38.0
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_EXACT_RUNNING_HEAD_BLOCKS = tuple(
    tuple(block.split("\n"))
    for block in (
        "28\n888\nWE AND OUR NEIGHBORS\n-",
        "38\n888\nWE AND OUR NEIGHBORS",
        "62\n22\nWE AND OUR NEIGHBORS",
        "68\n889\nWE AND OUR NEIGHBORS",
        'OUR ""\n135\n99\nPROJECTED',
        "OUR 'EVENING \" PROJECTED\n137",
        'OUR "EVENING" PROJECTED\n139',
        'OUR "\n141\nEVENING" PROJECTED',
        "AUNT MARIA ENDEAVORS TO SET MATTERS RIGHT\n223",
        "AUNT MARIA FREES HER MIND\n257",
        "WE MUST BE CAUTIOUS\n341",
        'WE MUST BE CAUTIOUS"\n343\n99',
        'WE MUST BE CAUTIOUS "\n345',
        "SAYS SHE TO HER NEIGHBOR - WHAT\n349",
        "THE VALLEY OF THE SHADOW\n397",
        '"IN THE FORGIVENESS OF SINS"\n413\n99\n-',
        '"IN THE FORGIVENESS OF SINS\n415\n""',
        '66 IN THE FORGIVENESS OF SINS"\n417',
        "WEDDING PRESENTS\n455",
        "MARRIED AND A'\n459",
    )
)
_PAGE_BREAK_WORD_JOINS = (
    ("car", "ried"),
    ("ad", "vantageous"),
    ("be", "longings"),
    ("ad", "mired"),
    ("his", "tory"),
    ("understand", "ing"),
    ("com", "menced"),
    ("investi", "gations"),
    ("obdu", "rately"),
    ("pos", "sibly"),
    ("recom", "mended"),
    ("infi", "nite"),
    ("mar", "riage"),
    ("intona", "tion"),
    ("in", "vited"),
    ("consola", "tion"),
    ("char", "acteristic"),
    ("daugh", "ter"),
    ("contin", "ued"),
    ("chat", "tering"),
    ("stay", "ing"),
    ("Look", "ing"),
    ("Phari", "sees"),
    ("bril", "liant"),
    ("accord", "ing"),
    ("rev", "erent"),
    ("Metho", "dist"),
    ("Wouver", "mans"),
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


def _remove_exact_running_head_blocks(text: str) -> str:
    lines = text.splitlines()
    dropped: set[int] = set()
    for block in _EXACT_RUNNING_HEAD_BLOCKS:
        width = len(block)
        for start in range(len(lines) - width + 1):
            if tuple(lines[start : start + width]) == block:
                dropped.update(range(start, start + width))
    return "\n".join(line for index, line in enumerate(lines) if index not in dropped)


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


class StoweWritings(BookProcessor):
    """
    Processor for The Writings of Harriet Beecher Stowe.
    """

    barcode = "32044094451689"
    title = "The Writings of Harriet Beecher Stowe"
    author = "Stowe, Harriet Beecher"
    date = "1896"

    notes = """
    Riverside Edition, Volume XIII of collected works.

    Known quirks:
    - Library stamps (Child Memorial Library, Harvard)
    - Multi-volume reference markers
    - Clean prose in main text
    - Some moral/philosophical essays
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
        """Book-specific cleanup for Writings of Harriet Beecher Stowe."""
        text = text.replace("OUR FIRST THURSDAY\n175was embarrassed", "was embarrassed")
        text = re.sub(r"(?m)^[ \t]*(?:✓|」|وو|دو|路|し)[ \t]*(?:\n|\Z)", "", text)
        text = text.replace("✓", "").replace("⚫", "")
        text = _remove_exact_running_head_blocks(text)
        text = _remove_recurrent_page_headers(text)
        text = _join_confirmed_page_break_words(text)
        text = text.replace("HIм", "HIM")
        text = text.replace("Ека.", "Eva.")
        text = text.replace("оссиру.", "occupy.")
        text = text.replace("Arthur, you❞—", 'Arthur, you"—')
        text = text.replace("d..grace", "disgrace")
        text = text.replace("selfesteem", "self-esteem")
        text = text.replace(
            'So, after dinner, Eva began with:-\n-\nsee.\n"Well',
            'So, after dinner, Eva began with:-\n"Well',
        )
        text = re.sub(r"\nThis book should be returned to\n[\s\S]*\Z", "", text)
        return re.sub(r"\n{3,}", "\n\n", text)
