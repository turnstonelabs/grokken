import pytest

from grokken.books.principia.algebra_day import (
    AlgebraDay,
)
from grokken.books.principia.algebra_day import (
    _remove_page_furniture as clean_algebra_furniture,
)
from grokken.books.principia.animal_histology_dahlgren import AnimalHistology
from grokken.books.principia.atonement import (
    Atonement,
)
from grokken.books.principia.atonement import (
    _remove_page_furniture as clean_atonement_furniture,
)
from grokken.books.principia.bible_literature_wood import BibleAsLiterature
from grokken.books.principia.channing_works import ChanningWorks
from grokken.books.principia.chaucer_student import (
    StudentChaucer,
)
from grokken.books.principia.chaucer_student import (
    _remove_page_furniture as clean_chaucer_furniture,
)
from grokken.books.principia.church_building_cram import ChurchBuilding
from grokken.books.principia.cornerstone_abbott import Cornerstone
from grokken.transforms import ocr

PROCESSORS = (
    AlgebraDay,
    AnimalHistology,
    Atonement,
    BibleAsLiterature,
    ChanningWorks,
    StudentChaucer,
    ChurchBuilding,
    Cornerstone,
)


@pytest.mark.parametrize("processor", PROCESSORS)
def test_broad_ocr_heuristics_are_not_used(processor):
    assert ocr.fix_digit_letter_confusion not in processor.transforms
    assert ocr.remove_ocr_artifacts not in processor.transforms


@pytest.mark.parametrize("processor", PROCESSORS)
def test_symbols_ellipses_repeated_letters_and_unpaired_numbers_survive(processor):
    source = "Body\n...\n=\nAAAAAA\n1\n2\n3"

    assert processor().process(source) == source


def test_algebra_preserves_digit_variables_and_rejects_false_folios():
    pages = [f"ALGEBRA.\n{folio}\nbody" for folio in range(42, 62)]
    source = "\n".join([*pages, *("content" for _ in range(5)), "805\nALGEBRA.\n1x1x1"])

    cleaned = clean_algebra_furniture(source)

    assert "42" not in cleaned
    assert "61" not in cleaned
    assert "805\nALGEBRA.\n1x1x1" in cleaned


def test_chaucer_page_sequence_does_not_delete_verse_numbers():
    pages = [f"The Romaunt of the Rose.\n{folio}\nverse" for folio in range(2, 17)]
    source = "\n".join([pages[0], "150", *pages[1:], "345"])

    cleaned = clean_chaucer_furniture(source)

    assert "\n2\n" not in cleaned
    assert "\n16\n" not in cleaned
    assert "150" in cleaned
    assert "345" in cleaned


def test_atonement_removes_sequential_roman_folios_but_not_section_numerals():
    roman_folios = (
        "x",
        "xi",
        "xii",
        "xiii",
        "xiv",
        "xv",
        "xvi",
        "xvii",
        "xviii",
        "xix",
        "xx",
        "xxi",
        "xxii",
        "xxiii",
        "xxiv",
        "xxv",
        "xxvi",
        "xxvii",
        "xxviii",
        "xxix",
    )
    pages = [f"{folio}\nINTRODUCTORY ESSAY.\nbody" for folio in roman_folios]
    source = "\n".join([*pages, "III"])

    cleaned = clean_atonement_furniture(source)

    assert "INTRODUCTORY ESSAY." not in cleaned
    assert "\nx\n" not in f"\n{cleaned}\n"
    assert "\nxxix\n" not in f"\n{cleaned}\n"
    assert cleaned.endswith("III")


def test_inspected_page_gap_words_are_rejoined_without_blanket_changes():
    assert "succeeding" in AlgebraDay().post_process(
        "PREFACE.\nTHE following summary\nsuc-\n\nceeding"
    )
    assert "illumination" in AnimalHistology().post_process(
        "INTRODUCTION\nA TEXT-BOOK of histology\nillumi-\n\nnation"
    )

    channing = ChanningWorks().post_process(
        "INTRODUCTORY REMARKS.\nTHE following tracts\ninsti-\n\ntution\nsub-\n\nthe"
    )
    assert "institution" in channing
    assert "sub-\n\nthe" in channing

    assert "mediæval" in ChurchBuilding().post_process(
        "PREFACE\nTHE greater portion\nmedi-\n\næval"
    )
    assert StudentChaucer().process("sheep-\nwine") == "sheep-\nwine"


def test_animal_histology_page_gap_dehyphenation_is_evidence_backed():
    source = (
        "INTRODUCTION\nA TEXT-BOOK of histology\n"
        "The muscle-\n\ncell remains hyphenated.\n"
        "These forms are pho-\n\nter. t.\nFIG. 122."
    )

    cleaned = AnimalHistology().post_process(source)

    assert "muscle-\n\ncell" not in cleaned
    assert "muscle-cell" in cleaned
    assert "pho-\n\nter. t." in cleaned
    assert "photer" not in cleaned


def test_channing_preserves_verified_anti_slavery_hyphenation():
    source = (
        "The antislavery movement appears throughout this volume.\n"
        "The periodical title is the Anti-Slavery Record.\n"
        "Its anti-\nslavery societies retained the edition's hyphen."
    )

    result = ChanningWorks().process(source)

    assert "anti-slavery societies" in result


@pytest.mark.parametrize(
    ("processor", "source", "kept", "removed"),
    (
        (
            AnimalHistology,
            "wrapper\nINTRODUCTION\nA TEXT-BOOK of histology\nkept\n"
            "AMONG RECENT SCIENTIFIC PUBLICATIONS\nremoved",
            "kept",
            "wrapper",
        ),
        (
            Atonement,
            "wrapper\nINTRODUCTORY ESSAY.\nTHERE is a theory\nkept\nEND.\nstamp",
            "kept\nEND.",
            "stamp",
        ),
        (
            BibleAsLiterature,
            "wrapper\nPREFACE\nTHIS book is designed\nkept\nJ\n\nS\n\nTHE BORROWER\nremoved",
            "kept",
            "THE BORROWER",
        ),
        (
            ChanningWorks,
            "wrapper\nINTRODUCTORY REMARKS.\nTHE following tracts\nkept\n"
            "Cambridge: Press of John Wilson & Son.\nremoved",
            "kept",
            "removed",
        ),
        (
            StudentChaucer,
            "wrapper\nINTRODUCTION.\nLIFE OF CHAUCER.\nkept\nTHE END.\nremoved",
            "kept\nTHE END.",
            "removed",
        ),
        (
            ChurchBuilding,
            "wrapper\nPREFACE\nTHE greater portion\nkept\n婴\nremoved",
            "kept",
            "removed",
        ),
    ),
)
def test_verified_scan_wrappers_are_trimmed(processor, source, kept, removed):
    cleaned = processor().post_process(source)

    assert kept in cleaned
    assert removed not in cleaned


def test_cornerstone_starts_at_complete_second_preface():
    marker = "PREFACE.\nTHE following work"
    source = f"wrapper\n{marker}\ninterrupted\n{marker}\nkept"

    cleaned = Cornerstone().post_process(source)

    assert cleaned.count(marker) == 1
    assert "interrupted" not in cleaned
    assert cleaned.endswith("kept")
