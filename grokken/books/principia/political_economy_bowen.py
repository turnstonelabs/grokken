"""
Handler for "The Principles of Political Economy" by Francis Bowen (1856).

Applied to the condition, resources, and institutions of the American people.

Score: 36.0
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_SAME_LINE_RUNNING_HEADS = (
    "THE AIMS AND ADVANTAGES OF POLITICAL ECONOMY.",
    "ADVANTAGES OF THE POSSESSION OF WEALTH.",
)
_EXACT_RUNNING_HEAD_BLOCKS = tuple(
    tuple(block.split("\n"))
    for block in (
        "40\nTHE PRODUCTION OF WEALTH.",
        "THE MEASURE OF VALUE.\n41",
        "54\nTHE MEASURE OF VALUE.",
        "112\nTHE DESIRE OF ACCUMULATION.",
        "130\nADVANTAGES OF THE POSSESSION OF WEALTH.",
        "334\nTHE DISTRIBUTION OF GOLD AND SILVER.",
        "456\nEFFECT OF SPECULATION ON PRICES.",
        "THE PROTECTIVE SYSTEM..\n469",
        "492\nINTERNATIONAL EXCHANGES.",
        "THE SUCCESSION TO PROPERTY..\n541",
    )
)
_PAGE_BREAK_WORD_JOINS = (
    ("metal", "lurgy"),
    ("inequal", "ities"),
    ("el", "evated"),
    ("ulti", "mate"),
    ("ob", "serve"),
    ("con", "sumed"),
    ("Civiliza", "tion"),
    ("cultiva", "tion"),
    ("famil", "iar"),
    ("re", "lieve"),
    ("jus", "tify"),
    ("be", "cause"),
    ("in", "crease"),
    ("how", "ever"),
    ("agri", "culture"),
    ("re", "cruit"),
    ("indus", "try"),
    ("du", "rable"),
    ("ex", "pense"),
    ("re", "serve"),
    ("trans", "fer"),
    ("imme", "diately"),
    ("de", "preciated"),
    ("numer", "ous"),
    ("ma", "chines"),
    ("be", "fore"),
    ("anxi", "ety"),
    ("effect", "ually"),
    ("occa", "sion"),
    ("opera", "tion"),
    ("advan", "tage"),
    ("legisla", "tive"),
    ("con", "nected"),
    ("conse", "quently"),
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
    for header in _SAME_LINE_RUNNING_HEADS:
        text = re.sub(
            rf"(?m)^[ \t]*{re.escape(header)}[ \t]+\d{{1,3}}[ \t]*(?:\n|\Z)",
            "",
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

    # Some late pages alternate between a blank-delimited head and a tightly
    # packed facing-page head. Two blank-delimited observations establish the
    # latter layout without treating a repeated table label as a running head.
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


class PoliticalEconomyBowen(BookProcessor):
    """
    Processor for The Principles of Political Economy (Bowen).
    """

    barcode = "32044018740308"
    title = "The Principles of Political Economy applied to the American people"
    author = "Bowen, Francis"
    date = "1856"

    notes = """
    American political economy focused on US conditions.

    Known quirks:
    - Discussion of agriculture, labor, production
    - American economic context
    - Statistical and economic terminology
    - References to civilized countries, inhabitants
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
        """Book-specific cleanup for Principles of Political Economy (Bowen)."""
        text = _remove_same_line_running_heads(text)
        text = _remove_recurrent_page_headers(text)
        text = _remove_exact_running_head_blocks(text)
        text = _join_confirmed_page_break_words(text)
        return re.sub(r"\n{3,}", "\n\n", text)
