"""
Handler for "The Vicarious Sacrifice" by Horace Bushnell (1866).

A theological work grounded in principles of universal obligation.

Score: 37.0
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
        "INTRODUCTION,\n17",
        "CHAP. II.\nTHE ETERNAL FATHER, ETC.\n57",
        "CHAP. III. IN VICARIOUS SACRIFICE.\n87",
        "90\nTHE HOLY SPIRIT, ETC.\nPART L.",
        "CHAP. IV. IN VICARIOUS SACRIFICE.\n95",
        "CHAP. IV. IN VICARIOUS SACRIFICE.\n103",
        "104\nTHE GOOD ANGELS, ETC.\nPART I.",
        "126\nALL SOULS REDEEMED, ETC.\nPART L.",
        "CHAP. III.\nIN WORKING SUCH RECOVERY.\n177",
        "CAP. III. IN WORKING SUCH RECOVERY.\n179",
        "CHAP. IV.\nSO GREAT A POWER,\n197",
        "CHAP III.\nTHE ANTAGONISM, ETC.\n267",
        "278\nTHE ANTAGONISM BETWEEN PART III",
        "284\nTHE ANTAGONISM BETWEEN PART III.",
        "292\nTHE ANTAGONISM BETWEEN PART III.",
        "294\nTHE ANTAGONISM BETWEEN PART IIL",
        "CHAP. IV. THE LAW PRECEPT, ETC.\n297",
        "CHAP. VI. GOD'S RECTORAL HONOR, ETC.\n365",
        "402\nPi.\nGOD'S RECTORAL HONOR, 220.",
        "412\nJUSTIFICATION BY FAITH. PART IIL.",
        "432\nJUSTIFICATION BY FAITH. PART III",
        "434\nJUSTIFICATION PART III.\nFICATION\nBY FAITH.",
        "CHAP. VII.\nJUSTIFICATION BY FAITH.'\n441",
        "СПАР. І. AND THE LUSTRAL FIGURES.\n479",
        "CHAP. L AND THE LUSTRAL FIGURES.\n481",
        "CHAP. II.\nATONEMENT,\nETC.\n483",
        "508\nPART IV\nATONEMENT, PROPITIATION,",
        "PART IV",
    )
)
_SIGNATURE_ONLY_BLOCKS = tuple(
    tuple(block.split("\n"))
    for block in (
        "7\n\nCHAPTER III.\nTHE HOLY SPIRIT IN VICARIOUS SACRIFICE.",
        "23\n\nCHAPTER III.\nTHE ANTAGONISM BETWEEN JUSTICE AND MERCY.",
        "41\n\nCHAPTER II.\nATONEMENT, PROPITIATION, AND EXPIATION.",
    )
)
_EXACT_ORPHAN_RUNNING_HEADS = frozenset(
    {
        "SO GREAT A POWER.",
        "AND EXPIATION.",
        "VICARIOUS SACRIFICE.",
        "NOT DIMINISHED.",
        "EFFECTIVELY MAINTAINED.",
        "IN VICARIOUS SACRIFICE.",
        "INSTITUTED GOVERNMENT.",
        "AND THE LUSTRAL FIGURES.",
        "JUSTICE AND MERCY.",
        "DULY SANCTIFIED.",
    }
)
_PAGE_BREAK_WORD_JOINS = (
    ("ex", "hibit"),
    ("watch", "ing"),
    ("Com", "forter"),
    ("sac", "rifice"),
    ("benevo", "lence"),
    ("spe", "cially"),
    ("under", "takes"),
    ("com", "monly"),
    ("na", "ture"),
    ("mat", "ters"),
    ("ever", "lastingly"),
    ("prece", "dence"),
    ("majes", "tic"),
    ("punish", "ment"),
    ("rela", "tionship"),
    ("con", "stitution"),
    ("practi", "cally"),
    ("refer", "ence"),
    ("ab", "horrence"),
    ("vanquish", "ed"),
    ("dishon", "ored"),
    ("mean", "ing"),
    ("es", "pecially"),
    ("lit", "tle"),
    ("him", "self"),
    ("con", "sciences"),
    ("Chris", "tian"),
    ("fol", "lowing"),
    ("retribu", "tive"),
    ("de", "molished"),
    ("intelli", "gence"),
    ("sup", "poses"),
    ("re", "mission"),
    ("contribu", "tion"),
    ("noth", "ing"),
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


def _drop_signature_for_folio(lines: list[str], folio_index: int, dropped: set[int]) -> None:
    if folio_index < 2 or lines[folio_index - 1].strip():
        return
    signature = lines[folio_index - 2].strip()
    folio = lines[folio_index].strip()
    if not signature.isdecimal() or not folio.isdecimal():
        return
    signature_number = int(signature)
    folio_number = int(folio)
    if 2 <= signature_number <= 46 and (
        folio_number == 12 * signature_number - 10 or (signature_number, folio_number) == (32, 874)
    ):
        dropped.add(folio_index - 2)


def _remove_exact_running_head_blocks(text: str) -> str:
    lines = text.splitlines()
    dropped: set[int] = set()
    for block in _EXACT_RUNNING_HEAD_BLOCKS:
        width = len(block)
        for start in range(len(lines) - width + 1):
            if tuple(lines[start : start + width]) != block:
                continue
            dropped.update(range(start, start + width))
            for offset, line in enumerate(block):
                if _FOLIO_LINE.fullmatch(line):
                    _drop_signature_for_folio(lines, start + offset, dropped)

    for block in _SIGNATURE_ONLY_BLOCKS:
        width = len(block)
        for start in range(len(lines) - width + 1):
            if tuple(lines[start : start + width]) == block:
                dropped.add(start)

    return "\n".join(line for index, line in enumerate(lines) if index not in dropped)


def _remove_exact_orphan_running_heads(text: str) -> str:
    lines = text.splitlines()
    dropped = {index for index, line in enumerate(lines) if line in _EXACT_ORPHAN_RUNNING_HEADS}
    for index, line in enumerate(lines):
        if line == "JUSTIFICATION BY FAITH." and (index == 0 or lines[index - 1] != "CHAPTER VII."):
            dropped.add(index)
    for index in range(len(lines) - 2):
        if tuple(lines[index : index + 3]) == ("Lien ..", "PART III.", "་"):
            dropped.add(index + 1)
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
        _drop_signature_for_folio(lines, folio_index, dropped)
        dropped.update((folio_index, *block))

    return "\n".join(line for index, line in enumerate(lines) if index not in dropped)


class VicariousSacrifice(BookProcessor):
    """
    Processor for The Vicarious Sacrifice.
    """

    barcode = "32044018647321"
    title = "The Vicarious Sacrifice, grounded in principles of universal obligation"
    author = "Bushnell, Horace"
    date = "1866"

    notes = """
    Theological treatise on atonement and sacrifice.

    Known quirks:
    - Religious/theological content
    - Biblical quotations and references
    - Dense theological prose
    - Phrases like "the wrath of the Lamb"
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
        """Book-specific cleanup for The Vicarious Sacrifice."""
        text = _remove_recurrent_page_headers(text)
        text = _remove_exact_running_head_blocks(text)
        text = _remove_exact_orphan_running_heads(text)
        text = _join_confirmed_page_break_words(text)
        text = text.replace("How дE BECOMES", "How HE BECOMES")
        text = text.replace("CHAPTER IV. ©", "CHAPTER IV.")
        text = text.replace("⚫", "")
        text = text.replace(
            "that he humanizes God to\nGod humanized men. I have already spoken of the nec-\n"
            "1\nto us. essary distance",
            "that he humanizes God to\nmen. I have already spoken of the necessary distance",
        )
        text = re.sub(r"(?m)^[ \t]*(?:心|眷|想|ا)[ \t]*(?:\n|\Z)", "", text)
        text = re.sub(r"\nTHE BORROWER WILL BE CHARGED\n[\s\S]*\Z", "", text)
        return re.sub(r"\n{3,}", "\n\n", text)
