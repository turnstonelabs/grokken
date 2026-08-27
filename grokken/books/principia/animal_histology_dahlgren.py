"""
Handler for "A Text-book of the Principles of Animal Histology" by Ulric Dahlgren (1908).

A scientific textbook on animal histology (microscopic anatomy of animal tissues).

Score: 38.0
"""

import regex as re

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

_RUNNING_HEADERS = frozenset(
    {
        "ADHESION AND SPINNING",
        "ALIMENTARY TISSUES",
        "AMITOSIS",
        "AMPLIFICATION OF EPITHELIAL SURFACES",
        "ATTRACTIVE AND REPULSIVE ODORS",
        "AUDITORY TISSUES",
        "BLOOD-FORMING GLANDS",
        "CARDIAC MUSCLE",
        "CIRCULATORY CHANNELS",
        "CIRCULATORY MEDIA",
        "CIRCULATORY TISSUES, GENERAL",
        "DIGESTIVE TISSUES",
        "ELECTRIC TISSUES, TELEOSTS",
        "EPITHELIUM",
        "FAT",
        "FEMALE REPRODUCTIVE CELLS",
        "GAS-SECRETING TISSUES",
        "GILLS",
        "GUSTATORY AND OLFACTORY TISSUES",
        "HIGHER RIGID SUPPORTING TISSUES",
        "HIGHER TENSILE CONNECTING TISSUES",
        "HISTOGENESIS OF STRIATED MUSCLE",
        "HISTOLOGY",
        "INDEX",
        "INTEGUMENT",
        "LUBRICATING TISSUES",
        "LUNGS",
        "MALE REPRODUCTIVE CELLS",
        "MECHANICAL PROTECTION AND POISONS",
        "MITOSIS",
        "MOTOR NERVE-ENDING",
        "MULTICELLULAR ORGANIZATION: PHYLOGENETIC",
        "NEPHRIDIAL TISSUES",
        "NERVE TISSUES",
        "NEUROGLIA",
        "NIDAMENTAL TISSUES",
        "NOURISHING MEMBRANES",
        "PIGMENT TISSUES",
        "SIMPLE RIGID SUPPORTING TISSUES",
        "SMOOTH MUSCLE",
        "STATIC TISSUES",
        "STRIATED MUSCLE",
        "TACTILE TISSUES",
        "TECHNIC",
        "THE DUCTLESS GLANDS",
        "THE NERVE CELL",
        "THE NERVE FIBER",
        "THE TISSUES OF MOTION",
        "TISSUES OF LIGHT-PRODUCTION",
        "VISUAL TISSUES",
    }
)
_FOLIO_RANGE = range(1, 516)
_MIN_FOLIO_SEQUENCE = 20


def _remove_page_furniture(text: str) -> str:
    """Remove exact running labels only on a long monotone folio sequence."""
    lines = text.splitlines()
    header_indices = [index for index, line in enumerate(lines) if line.strip() in _RUNNING_HEADERS]
    candidates: list[tuple[int, int, set[int]]] = []
    for index, line in enumerate(lines):
        if not re.fullmatch(r"[ \t]*\d{1,4}[ \t]*", line):
            continue
        headers = {header for header in header_indices if abs(header - index) <= 4}
        value = int(line.strip())
        if headers and value in _FOLIO_RANGE:
            candidates.append((index, value, headers))

    forward = [1] * len(candidates)
    for position, (index, value, _) in enumerate(candidates):
        for prior in range(position - 1, -1, -1):
            prior_index, prior_value, _ = candidates[prior]
            if index - prior_index > 700:
                break
            if 0 < value - prior_value <= 4:
                forward[position] = max(forward[position], forward[prior] + 1)

    backward = [1] * len(candidates)
    for position in range(len(candidates) - 1, -1, -1):
        index, value, _ = candidates[position]
        for following in range(position + 1, len(candidates)):
            following_index, following_value, _ = candidates[following]
            if following_index - index > 700:
                break
            if 0 < following_value - value <= 4:
                backward[position] = max(backward[position], backward[following] + 1)

    clear: set[int] = set()
    for position, (index, value, headers) in enumerate(candidates):
        sequence_length = forward[position] + backward[position] - 1
        ambiguous = any(
            other_index != index and other_value == value and abs(other_index - index) <= 700
            for other_index, other_value, _ in candidates
        )
        if sequence_length >= _MIN_FOLIO_SEQUENCE and not ambiguous:
            clear.update({index, *headers})
    return "\n".join(line for index, line in enumerate(lines) if index not in clear)


class AnimalHistology(BookProcessor):
    """
    Processor for A Text-book of the Principles of Animal Histology.
    """

    barcode = "HN2WWN"
    title = "A Text-book of the Principles of Animal Histology"
    author = "Dahlgren, Ulric"
    date = "1908"

    notes = """
    Scientific textbook on animal histology.

    Known quirks:
    - Many figure references and diagram descriptions
    - Running headers "HISTOLOGY"
    - Technical terminology (rods, cones, cells, etc.)
    - References to other texts (Stohr's Text-book, Lewis)
    - Abbreviations in figure legends (bl.v., pg., etc.)
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Principles of Animal Histology."""
        front_marker = "INTRODUCTION\nA TEXT-BOOK of histology"
        front_pos = text.find(front_marker)
        if front_pos > 0:
            text = text[front_pos:]

        # Publisher advertisements follow the terminal Zygote index entry.
        back_marker = "\nAMONG RECENT SCIENTIFIC PUBLICATIONS"
        back_pos = text.find(back_marker)
        if back_pos > 0:
            text = text[:back_pos]

        text = _remove_page_furniture(text)

        # Removing page furniture exposes both genuine word wraps and figure-label
        # collisions. Join only independently attested words, while retaining the
        # edition's lexical ``muscle-cell`` spelling.
        text = whitespace.dehyphenate_attested_page_gaps(
            text,
            preserve_hyphenated=("muscle-cell",),
        )

        # The sole clear page-gap join without independent in-book attestation.
        text = text.replace("illumi-\n\nnation", "illumination")

        return whitespace.collapse_blank_lines(max_consecutive=2)(text).strip()
