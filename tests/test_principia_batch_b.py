"""Focused regressions for the Principia batch-B handlers."""

import pytest

from grokken.books.principia.dickens_works import DickensWorks
from grokken.books.principia.doctrines_friends_bates import DoctrinesOfFriends
from grokken.books.principia.english_literature_shaw import EnglishLiterature
from grokken.books.principia.ethics_jouffroy import IntroductionToEthics
from grokken.books.principia.evolution_conn import EvolutionToday
from grokken.books.principia.hermeneutical_manual_fairbairn import HermeneuticalManual
from grokken.books.principia.history_religions_toy import HistoryOfReligions
from grokken.books.principia.international_law_davis_1900 import InternationalLawDavis1900

HANDLER_CASES = [
    (DickensWorks, "THE PICKWICK CLUB.", "ིའི་"),
    (DoctrinesOfFriends, "THE SCRIPTURES.", "解"),
    (EnglishLiterature, "SHAKSPEARE.", "ザ"),
    (IntroductionToEthics, "SYSTEM OF PANTHEISM.", "典"),
    (EvolutionToday, "EVOLUTION OF TO-DA Y.", "蘼"),
    (HermeneuticalManual, "OLD TESTAMENT IN THE NEW.", "Ꮓ"),
    (HistoryOfReligions, "TOTEMISM AND TABOO", "عيرة"),
    (InternationalLawDavis1900, "THE LAW OF WAR", "の"),
]


@pytest.mark.parametrize(("processor", "header", "garbage"), HANDLER_CASES)
def test_removes_only_numbered_allowlisted_headers(processor, header, garbage):
    fixture = f"Opening prose.\n\n{header}\n43\ncontinued prose.\n\n{header}\nReal heading."

    result = processor().post_process(fixture)

    assert "43" not in result
    assert result.count(header) == 1
    assert f"{header}\nReal heading." in result


@pytest.mark.parametrize(("processor", "header", "garbage"), HANDLER_CASES)
def test_preserves_unpaired_numbers_symbols_and_repeated_content(processor, header, garbage):
    fixture = "Verse or section\n\n42\n\nA\n\n§\n\n......\n\nsooooo\n\n1x1x1\n\nEnd"

    result = processor().process(fixture)

    for retained in ("42", "A", "§", "......", "sooooo", "1x1x1"):
        assert retained in result


@pytest.mark.parametrize(("processor", "header", "garbage"), HANDLER_CASES)
def test_removes_only_exact_confirmed_scan_garbage(processor, header, garbage):
    fixture = f"Before\n{garbage}\nAfter\nword{garbage}word"

    result = processor().post_process(fixture)

    assert f"\n{garbage}\n" not in f"\n{result}\n"
    assert f"word{garbage}word" in result


def test_dickens_repairs_quote_glyphs_and_trims_due_slip():
    fixture = (
        '،، Gone!" exclaimed Mr. Pickwick.\n،،\nYou will excuse me.\nStory end.\nNG\n•\n'
        "THE BORROWER WILL BE CHARGED\nDATE STAMP"
    )

    result = DickensWorks().post_process(fixture)

    assert result == '"Gone!" exclaimed Mr. Pickwick.\n"You will excuse me.\nStory end.'


def test_dickens_dominant_joined_spelling_outweighs_stray_hyphenation():
    source = (
        ("Pickwick " * 8)
        + "appears beside one Pick-wick variant.\n"
        + "The next Pick-\nwick occurrence follows the dominant spelling."
    )

    result = DickensWorks().process(source)

    assert "next Pickwick occurrence" in result
    assert result.count("Pick-wick") == 1


def test_doctrines_trims_library_slip_after_explicit_end():
    result = DoctrinesOfFriends().post_process("Doctrine.\nTHE END.\nBOOK DUE")

    assert result == "Doctrine.\nTHE END."


def test_english_literature_repairs_names_and_page_split():
    fixture = "Sтow, Toм BROWN, РоMFRET, POмfret, and Ноок.\nRo-\n\nmanorum."

    result = EnglishLiterature().post_process(fixture)

    assert "STOW, TOM BROWN, POMFRET, POMFRET, and HOOK." in result
    assert "Romanorum." in result


def test_english_literature_removes_two_anchored_scan_fragments():
    fixture = (
        "chapters, the first of which he wrote thrice, and the second twice over,\n"
        "ܢ\nJ\n30\n20nd\nA. D. 1737-1794.]\nBody.\n"
        "- every feature of his character heightens the charm of this most fascinating book.\n"
        "كم\nT-\n}\nb\nE\nCHAP. XVIII.]\nNotes."
    )

    result = EnglishLiterature().post_process(fixture)

    assert "twice over,\nA. D. 1737-1794.]" in result
    assert "book.\nCHAP. XVIII.]" in result
    for noise in ("ܢ", "20nd", "كم", "T-\n}"):
        assert noise not in result


def test_english_literature_trims_due_slip_after_index():
    result = EnglishLiterature().post_process(
        "Young, 490.\nThis book should be returned to\nDATE STAMP"
    )

    assert result == "Young, 490."


def test_ethics_uses_book_boundaries_and_repairs_title():
    fixture = (
        "HANDWRITTEN SCAN\nSPECIMENS\nOF\nFOREIGN STANDARD LITERATURE.\n"
        "INTRODUCTION\nто\nETHICS,\nBody.\nEND OF VOL. I.\nLIBRARY STAMP"
    )

    result = IntroductionToEthics().post_process(fixture)

    assert result.startswith("SPECIMENS\nOF\nFOREIGN STANDARD LITERATURE.")
    assert "INTRODUCTION\nTO\nETHICS," in result
    assert result.endswith("END OF VOL. I.")
    assert "HANDWRITTEN" not in result
    assert "LIBRARY STAMP" not in result


def test_ethics_removes_only_paired_volume_signatures():
    fixture = "Body.\nVOL. I.\nU\n\nContinued.\n\nVOL. I.\nReal heading.\n\n+\nSymbol."

    result = IntroductionToEthics().post_process(fixture)

    assert result == "Body.\n\nContinued.\n\nVOL. I.\nReal heading.\n\n+\nSymbol."


def test_evolution_trims_library_slip_after_index():
    result = EvolutionToday().post_process(
        "Zoological regions, 176\nThis book should be returned to\nDATE STAMP"
    )

    assert result == "Zoological regions, 176"


def test_hermeneutical_manual_repairs_inspected_greek_and_page_splits():
    fixture = "λόγ-\nος\nhea-\n\nven\nGos-\n\npels\nmisinter-\n\npreted\nTesta-\n\nment"

    result = HermeneuticalManual().post_process(fixture)

    assert result == "λόγος\nheaven\nGospels\nmisinterpreted\nTestament"


def test_hermeneutical_manual_removes_exact_page_heads_not_real_headings():
    fixture = (
        "Body.\n314\nTHE USE OF βαπτίζω.\nContinued.\n\n"
        "EPHESIANS.\n441\nMore.\n\nEPHESIANS.\nReal section."
    )

    result = HermeneuticalManual().post_process(fixture)

    assert "314" not in result
    assert "441" not in result
    assert "THE USE OF βαπτίζω." not in result
    assert result.count("EPHESIANS.") == 1
    assert "EPHESIANS.\nReal section." in result


def test_history_of_religions_repairs_two_inspected_page_splits():
    fixture = "Aphro-\n\nditon\nthe vic-\n\nof Judas over that general"

    result = HistoryOfReligions().post_process(fixture)

    assert result == "Aphroditon\nthe victory of Judas over that general"


def test_history_of_religions_trims_due_slip_after_index():
    result = HistoryOfReligions().post_process("Zoroastrianism, 1109\nDATE DUE\nSTAMP")

    assert result == "Zoroastrianism, 1109"


def test_international_law_repairs_page_splits_and_trims_library_plate():
    fixture = "Phi-\n\nlology\nto de-\n\ntain\nTHE END\nHARVARD LAW LIBRARY"

    result = InternationalLawDavis1900().post_process(fixture)

    assert result == "Philology\nto detain\nTHE END"
