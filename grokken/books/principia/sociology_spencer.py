"""
Handler for "The Principles of Sociology" by Herbert Spencer (1895).

Spencer's foundational work applying evolutionary principles to social organization.

Score: 37.9
"""

import unicodedata
from collections import Counter, defaultdict

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, typography, whitespace

_FOLIO_LINE = re.compile(r"^\s*\d{1,4}\s*$")
_SAME_LINE_RUNNING_HEADS = (
    "SACRED PLACES, TEMPLES, AND ALTARS; ETC.",
    "INSPIRATION, DIVINATION, EXORCISM, AND SORCERY.",
    "THE IDEAS OF SOULS, GHOSTS, SPIRITS, DEMONS, ETC.",
    "SUPERNATURAL AGENTS AS CAUSING EPILEPSY, ETC.",
    "DIVERSE INTERESTS OF SPECIES, PARENTS, ETC.",
)
_EXACT_CORRUPT_RUNNING_HEADS = (
    "THE DATA OF SOCIOLOGT.",
    "TIIE DATA OF SOCIOLOGY.",
)
_PAGE_BREAK_WORD_JOINS = (
    ("depre", "dations"),
    ("sensa", "tions"),
    ("corre", "spondence"),
    ("revenge", "ful"),
    ("down", "wards"),
    ("ani", "mation"),
    ("inaccessi", "bility"),
    ("explana", "tion"),
    ("charac", "ter"),
    ("sup", "port"),
    ("implica", "tion"),
    ("ances", "tor"),
    ("re", "versed"),
    ("interpreta", "tion"),
    ("every", "where"),
    ("nick", "names"),
    ("individu", "alized"),
    ("mis", "construction"),
    ("tradi", "tional"),
    ("agri", "culture"),
    ("super", "naturally"),
    ("abso", "lutely"),
    ("mem", "bers"),
    ("co", "ordinated"),
    ("cor", "porate"),
    ("mat", "ters"),
    ("indus", "tries"),
    ("differen", "tiations"),
    ("chief", "tainships"),
    ("evolu", "tion"),
    ("diffi", "cult"),
    ("indus", "trial"),
    ("un", "fold"),
    ("govern", "mental"),
    ("pro", "tecting"),
    ("ac", "counts"),
    ("Sep", "tember"),
    ("poly", "andry"),
    ("con", "firmatory"),
    ("ap", "propriation"),
    ("instru", "mentality"),
    ("ap", "proaching"),
    ("dis", "playing"),
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
    for header in _SAME_LINE_RUNNING_HEADS:
        text = re.sub(
            rf"(?m)^[ \t]*{re.escape(header)}[ \t]+\d{{3}}[ \t]*(?:\n|\Z)",
            "",
            text,
        )
    for header in _EXACT_CORRUPT_RUNNING_HEADS:
        text = re.sub(rf"(?m)^[ \t]*{re.escape(header)}[ \t]*(?:\n|\Z)", "", text)
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


class SociologySpencer(BookProcessor):
    """
    Processor for The Principles of Sociology.
    """

    barcode = "32044020258091"
    title = "The Principles of Sociology"
    author = "Spencer, Herbert"
    date = "1895"

    notes = """
    Spencer's evolutionary sociology work.

    Known quirks:
    - Scientific/philosophical prose
    - Discussion of biological and social evolution
    - Technical terminology
    - Running headers likely present
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
        """Book-specific cleanup for Principles of Sociology."""
        text = _remove_exact_page_furniture(text)
        text = _remove_recurrent_page_headers(text)
        text = _join_confirmed_page_break_words(text)
        text = text.replace(
            "language its changes bave been changes of form",
            "language its changes have been changes of form",
        )
        text = text.replace("incon\ngruous", "incongruous")
        text = text.replace("voiumi-\n\nnous", "voluminous")
        text = text.replace("under-\n\nground burial places", "underground burial places")
        text = text.replace("medi-\næval", "mediæval")
        # The edition immediately repeats this technical term with an inline
        # hyphen; local context overrides the otherwise dominant joined form.
        text = text.replace(
            "significantly called internuncial). It is fulfilled in societies",
            "significantly called inter-nuncial). It is fulfilled in societies",
        )
        return re.sub(r"\n{3,}", "\n\n", text)
