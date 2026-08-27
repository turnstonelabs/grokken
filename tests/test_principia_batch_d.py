"""Regressions for the Phase 0 quality audit, Principia batch D."""

import pytest

from grokken.books.principia.political_economy_bowen import PoliticalEconomyBowen
from grokken.books.principia.political_economy_mill_1870 import PoliticalEconomyMill1870
from grokken.books.principia.political_economy_mill_1884 import PoliticalEconomyMill1884
from grokken.books.principia.political_science_leacock import PoliticalScience
from grokken.books.principia.sociology_giddings import SociologyGiddings
from grokken.books.principia.sociology_spencer import SociologySpencer
from grokken.books.principia.stowe_writings import StoweWritings
from grokken.books.principia.vicarious_sacrifice_bushnell import VicariousSacrifice

PROCESSORS_AND_HEADERS = [
    (PoliticalEconomyBowen, "BANKS AND BANK CURRENCY."),
    (PoliticalEconomyMill1870, "PEASANT PROPRIETORS."),
    (PoliticalEconomyMill1884, "LIMITS OF THE PROVINCE OF GOVERNMENT."),
    (PoliticalScience, "THE NATURE OF THE STATE"),
    (SociologyGiddings, "The Elements of Sociology"),
    (SociologySpencer, "THE DATA OF SOCIOLOGY."),
    (StoweWritings, "WE AND OUR NEIGHBORS"),
    (VicariousSacrifice, "PART III."),
]


@pytest.mark.parametrize(("processor_type", "running_header"), PROCESSORS_AND_HEADERS)
def test_recurrent_page_headers_are_removed_without_losing_real_heading(
    processor_type: type, running_header: str
) -> None:
    text = (
        "opening text\n\n"
        f"42\n{running_header}\ncontinued text\n"
        f"body text\n\n{running_header}\n43\nmore text\n"
        f"tightly packed facing page\n44\n{running_header}\nending text\n\n"
        f"{running_header}\nsection opening"
    )

    result = processor_type().process(text)

    assert result.count(running_header) == 1
    assert "continued text" in result
    assert "more text" in result
    assert "ending text" in result
    assert "section opening" in result
    assert not {"42", "43", "44"} & set(result.splitlines())


@pytest.mark.parametrize(
    ("processor_type", "running_header", "left", "right", "joined"),
    [
        (PoliticalEconomyBowen, "BANKS AND BANK CURRENCY.", "metal", "lurgy", "metallurgy"),
        (PoliticalEconomyMill1870, "PEASANT PROPRIETORS.", "pre", "vailed", "prevailed"),
        (
            PoliticalEconomyMill1884,
            "LIMITS OF THE PROVINCE OF GOVERNMENT.",
            "pro",
            "duction",
            "production",
        ),
        (PoliticalScience, "THE NATURE OF THE STATE", "be", "ginning", "beginning"),
        (SociologyGiddings, "The Elements of Sociology", "dis", "appear", "disappear"),
        (SociologySpencer, "THE DATA OF SOCIOLOGY.", "depre", "dations", "depredations"),
        (StoweWritings, "WE AND OUR NEIGHBORS", "car", "ried", "carried"),
        (VicariousSacrifice, "PART III.", "ex", "hibit", "exhibit"),
    ],
)
def test_only_context_verified_page_break_words_are_rejoined(
    processor_type: type,
    running_header: str,
    left: str,
    right: str,
    joined: str,
) -> None:
    text = (
        f"the {left}-\n\n42\n{running_header}\n{right} example\n"
        f"body\n\n{running_header}\n43\nmore\n"
        f"body\n\n44\n{running_header}\nend"
    )

    result = processor_type().process(text)

    assert f"the {joined} example" in result


@pytest.mark.parametrize(
    ("processor_type", "running_header", "left", "right"),
    [
        (PoliticalEconomyBowen, "BANKS AND BANK CURRENCY.", "long", "neglected"),
        (PoliticalEconomyMill1870, "PEASANT PROPRIETORS.", "show", "all"),
        (
            PoliticalEconomyMill1884,
            "LIMITS OF THE PROVINCE OF GOVERNMENT.",
            "one",
            "fifth",
        ),
        (PoliticalScience, "THE NATURE OF THE STATE", "com", "schli"),
        (SociologyGiddings, "The Elements of Sociology", "distinc", "and"),
        (SociologySpencer, "THE DATA OF SOCIOLOGY.", "year", "old"),
        (StoweWritings, "WE AND OUR NEIGHBORS", "self", "willed"),
        (VicariousSacrifice, "PART III.", "sacri", "lan"),
    ],
)
def test_ambiguous_or_intentional_hyphens_are_not_rejoined(
    processor_type: type, running_header: str, left: str, right: str
) -> None:
    text = (
        f"the {left}-\n\n42\n{running_header}\n{right} example\n"
        f"body\n\n{running_header}\n43\nmore\n"
        f"body\n\n44\n{running_header}\nend"
    )

    result = processor_type().process(text)

    assert f"the {left}-\n\n{right} example" in result


@pytest.mark.parametrize("processor_type", [item[0] for item in PROCESSORS_AND_HEADERS])
def test_unmatched_numbers_and_nonboundary_repeated_labels_are_preserved(
    processor_type: type,
) -> None:
    text = (
        "CONTENTS\nChapter One\n42\n"
        "Table: Year | Value\n1898\n1\n2\n"
        "Footnote\n12\nSource note\n"
        "REPEATED CONTENT LABEL\n7\nfirst cell\n"
        "REPEATED CONTENT LABEL\n8\nsecond cell\n"
        "REPEATED CONTENT LABEL\n9\nthird cell"
    )

    result = processor_type().process(text)

    for value in ("42", "1898", "1", "2", "12", "7", "8", "9"):
        assert value in result.splitlines()
    assert result.count("REPEATED CONTENT LABEL") == 3


@pytest.mark.parametrize("processor_type", [item[0] for item in PROCESSORS_AND_HEADERS])
def test_broad_ocr_cleanup_does_not_delete_intentional_content(processor_type: type) -> None:
    text = 'Quoted dialect: "I bave no answer."\n...\n*\nAAAAA\nGrid 1x1 and A0B.'

    result = processor_type().process(text)

    assert '"I bave no answer."' in result
    assert "..." in result
    assert "*" in result.splitlines()
    assert "AAAAA" in result
    assert "1x1" in result
    assert "A0B" in result


@pytest.mark.parametrize("processor_type", [PoliticalScience, SociologySpencer])
def test_medi_aelig_word_is_rejoined(processor_type: type) -> None:
    assert processor_type().process("the medi-\næval period") == "the mediæval period"


def test_leacock_repairs_one_context_verified_interleaving_error() -> None:
    text = (
        "with a view to discov-\n\n245\nFEDERAL GOVERNMENT\nmay\n"
        "ering the teaching of experience\n"
        "body\n\nFEDERAL GOVERNMENT\n247\nmore\n"
        "body\n\n249\nFEDERAL GOVERNMENT\nend"
    )

    result = PoliticalScience().process(text)

    assert "with a view to discovering the teaching of experience" in result
    assert "FEDERAL GOVERNMENT" not in result


def test_spencer_repairs_one_context_verified_ocr_word() -> None:
    text = "language its changes bave been changes of form"

    assert SociologySpencer().process(text) == "language its changes have been changes of form"


def test_spencer_local_hyphen_evidence_overrides_global_frequency() -> None:
    source = (
        ("internuncial " * 10)
        + "appears once as inter-nuncial. The function was significantly called "
        + "inter-\nnuncial). It is fulfilled in societies."
    )

    result = SociologySpencer().process(source)

    assert "significantly called inter-nuncial). It is fulfilled" in result


def test_bowen_repairs_confirmed_unhyphenated_word_wrap() -> None:
    source = (
        "came to be consid\nered as farms\n"
        "level your pre-\nferments\n"
        "operating unim-\npeded\n"
        "СНАРТЕR IX.\n"
        "consider this separate line"
    )

    result = PoliticalEconomyBowen().process(source)

    assert result == (
        "came to be considered as farms\n"
        "level your preferments\n"
        "operating unimpeded\n"
        "CHAPTER IX.\n"
        "consider this separate line"
    )


def test_stowe_removes_only_context_verified_scan_marks() -> None:
    text = (
        "first sentence\n✓\ncontinues\nsecond sentence\n」\ncontinues\n"
        "the rev-✓\nerent Methodist had his ✓ bread\n⚫ which\n*\n—\n..."
    )

    result = StoweWritings().process(text)

    assert "✓" not in result
    assert "」" not in result
    assert "first sentence\ncontinues" in result
    assert "second sentence\ncontinues" in result
    assert "the reverent Methodist had his  bread" in result
    assert "which" in result
    assert "*" in result.splitlines()
    assert "—" in result.splitlines()
    assert "..." in result.splitlines()


@pytest.mark.parametrize(
    ("processor_type", "furniture", "real_heading"),
    [
        (
            PoliticalEconomyBowen,
            "THE AIMS AND ADVANTAGES OF POLITICAL ECONOMY. 127",
            "THE AIMS AND ADVANTAGES OF POLITICAL ECONOMY.",
        ),
        (
            PoliticalEconomyMill1870,
            "PRODUCTION ON A LARGE AND ON A SMALL SCALE. 143",
            "PRODUCTION ON A LARGE AND ON A SMALL SCALE.",
        ),
        (
            PoliticalEconomyMill1884,
            "PROBABLE FUTURE OF THE LABOURING CLASSES. 521",
            "PROBABLE FUTURE OF THE LABOURING CLASSES.",
        ),
        (
            PoliticalScience,
            "211 THE STRUCTURE OF THE GOVERNMENT`",
            "THE STRUCTURE OF THE GOVERNMENT",
        ),
        (
            SociologyGiddings,
            "Formal Like-mindedness: Tradition and Conformity 147",
            "Formal Like-mindedness: Tradition and Conformity",
        ),
        (
            SociologySpencer,
            "SACRED PLACES, TEMPLES, AND ALTARS; ETC. 523",
            "SACRED PLACES, TEMPLES, AND ALTARS; ETC.",
        ),
    ],
)
def test_exact_same_line_running_heads_are_removed_but_real_headings_remain(
    processor_type: type, furniture: str, real_heading: str
) -> None:
    result = processor_type().process(f"opening\n{furniture}\nbody\n{real_heading}\nsection")

    assert furniture not in result
    assert real_heading in result.splitlines()


@pytest.mark.parametrize(
    ("processor_type", "volume", "footer"),
    [
        (PoliticalEconomyMill1870, "BOOK I.", "VOL. I. — 22"),
        (PoliticalEconomyMill1884, "BOOK II.", "VOL. II. - -57"),
    ],
)
def test_mill_running_book_chapter_and_quire_lines_are_removed(
    processor_type: type, volume: str, footer: str
) -> None:
    text = f"opening\n217\n$ 3.\nBOOK 1, CHAPTER 4, - $ 1.\n§ 5.\n{footer}\n{volume}\nPRODUCTION."

    result = processor_type().process(text)

    assert "BOOK 1, CHAPTER 4, - $ 1." not in result
    assert "217" not in result.splitlines()
    assert "$ 3." not in result.splitlines()
    assert "§ 5." not in result.splitlines()
    assert footer not in result
    assert volume in result.splitlines()
    assert "PRODUCTION." in result.splitlines()


def test_giddings_drops_only_verified_clipped_column_fragments() -> None:
    coherent = "This coherent sentence is longer than forty characters and must remain."
    text = f"before\n237\nshort shard\nanother shard\n{coherent}\nafter"

    result = SociologyGiddings().process(text)

    assert "short shard" not in result
    assert "another shard" not in result
    assert "237" not in result.splitlines()
    assert coherent in result
    assert "after" in result


@pytest.mark.parametrize("folio", ["247", "269"])
def test_giddings_preserves_clipped_column_exception_pages(folio: str) -> None:
    text = f"before\n{folio}\nshort but coherent source line\nafter"

    result = SociologyGiddings().process(text)

    assert folio in result.splitlines()
    assert "short but coherent source line" in result


def test_bushnell_exact_low_frequency_head_exposes_only_confirmed_join() -> None:
    text = "before him-\n\nCHAP. II.\nTHE ETERNAL FATHER, ETC.\n57\nself after"

    result = VicariousSacrifice().process(text)

    assert result == "before himself after"


def test_bushnell_signature_is_removed_only_with_confirmed_page_layout() -> None:
    text = (
        "4\n\n38\nPART I.\nTHE MEANING OF\nbody\n\n"
        "50\nPART I.\nTHE MEANING OF\nbody\n\n"
        "62\nPART I.\nTHE MEANING OF\nbody\n"
        "Table\n4\n\n38\nordinary body"
    )

    result = VicariousSacrifice().process(text)

    assert result.splitlines().count("4") == 1
    assert "Table\n4\n\n38\nordinary body" in result


def test_bushnell_signature_only_exception_preserves_real_heading() -> None:
    text = "7\n\nCHAPTER III.\nTHE HOLY SPIRIT IN VICARIOUS SACRIFICE.\nbody"

    result = VicariousSacrifice().process(text)

    assert "7" not in result.splitlines()
    assert "CHAPTER III." in result.splitlines()
    assert "THE HOLY SPIRIT IN VICARIOUS SACRIFICE." in result.splitlines()


def test_bushnell_orphan_heads_preserve_real_chapter_and_part_headings() -> None:
    text = (
        "body\nSO GREAT A POWER.\ncontinues\n"
        "body\nJUSTIFICATION BY FAITH.\ncontinues\n"
        "CHAPTER VII.\nJUSTIFICATION BY FAITH.\nreal chapter\n"
        "Lien ..\nPART III.\n་\nbody\nPART III.\nreal part"
    )

    result = VicariousSacrifice().process(text)

    assert "SO GREAT A POWER." not in result
    assert result.count("JUSTIFICATION BY FAITH.") == 1
    assert "CHAPTER VII.\nJUSTIFICATION BY FAITH." in result
    assert result.count("PART III.") == 1
    assert "PART III.\nreal part" in result


def test_book_local_ocr_repairs_are_exact_and_preserve_near_misses() -> None:
    leacock = PoliticalScience().process(
        "Ghe Riverside Press\nsays\nsays the\nsame authority\n99 66\nGhe elsewhere"
    )
    giddings = SociologyGiddings().process("Il success\nhigh de-`\nvelopment\nIl successful")
    spencer = SociologySpencer().process("incon\ngruous\nbave quoted\nsevlapivs")

    assert "The Riverside Press" in leacock
    assert "says the\nsame authority" in leacock
    assert "99 66" not in leacock
    assert "Ghe elsewhere" in leacock
    assert "Ill success" in giddings
    assert "high development" in giddings
    assert "Il successful" in giddings
    assert "incongruous" in spencer
    assert "bave quoted" in spencer
    assert "sevlapivs" in spencer


@pytest.mark.parametrize(
    ("processor_type", "tail_anchor"),
    [
        (StoweWritings, "This book should be returned to"),
        (VicariousSacrifice, "THE BORROWER WILL BE CHARGED"),
    ],
)
def test_exact_library_tail_is_trimmed_after_book_text(
    processor_type: type, tail_anchor: str
) -> None:
    result = processor_type().process(
        f"final words of the book\n{tail_anchor}\nDUE DATE\nJUN 12 1967"
    )

    assert result == "final words of the book"


def test_bushnell_preserves_toc_leaders_and_page_reference() -> None:
    text = "CONTENTS\nAtonement, Propitiation, ........ 185\nnext entry"

    result = VicariousSacrifice().process(text)

    assert "........ 185" in result


def test_exact_interleaved_margin_fragments_are_removed() -> None:
    stowe = StoweWritings().post_process(
        'So, after dinner, Eva began with:-\n-\nsee.\n"Well, you know"'
    )
    bushnell = VicariousSacrifice().post_process(
        "that he humanizes God to\nGod humanized men. I have already spoken of the nec-\n"
        "1\nto us. essary distance and coldness"
    )

    assert stowe == 'So, after dinner, Eva began with:-\n"Well, you know"'
    assert bushnell == (
        "that he humanizes God to\n"
        "men. I have already spoken of the necessary distance and coldness"
    )


def test_stowe_removes_fused_folio_and_running_head_seam() -> None:
    text = "before\nOUR FIRST THURSDAY\n175was embarrassed by the scene\nafter"

    result = StoweWritings().post_process(text)

    assert "OUR FIRST THURSDAY" not in result
    assert "175was" not in result
    assert "was embarrassed by the scene" in result


def test_stowe_exact_low_frequency_page_head_preserves_real_heading() -> None:
    text = (
        'the Wouver-\n\n"IN THE FORGIVENESS OF SINS"\n413\n99\n-\nmans picture\n'
        '"IN THE FORGIVENESS OF SINS"\nchapter opening'
    )

    result = StoweWritings().process(text)

    assert "the Wouvermans picture" in result
    assert result.count('"IN THE FORGIVENESS OF SINS"') == 1


def test_stowe_dual_number_page_blocks_are_removed_before_recurrence() -> None:
    text = (
        "28\n888\nWE AND OUR NEIGHBORS\n-\nfirst continuation\n"
        "38\n888\nWE AND OUR NEIGHBORS\nsecond continuation\n"
        "62\n22\nWE AND OUR NEIGHBORS\nthird continuation\n"
        "68\n889\nWE AND OUR NEIGHBORS\nfourth continuation"
    )

    result = StoweWritings().process(text)

    assert not {"28", "38", "62", "68", "888", "22", "889"} & set(result.splitlines())
    for ordinal in ("first", "second", "third", "fourth"):
        assert f"{ordinal} continuation" in result


@pytest.mark.parametrize(
    ("processor_type", "page_block", "real_heading"),
    [
        (
            PoliticalEconomyBowen,
            "40\nTHE PRODUCTION OF WEALTH.",
            "THE PRODUCTION OF WEALTH.",
        ),
        (
            PoliticalEconomyMill1870,
            "FOURIERISM.\n275",
            "FOURIERISM.",
        ),
        (
            PoliticalEconomyMill1884,
            "USURY LAWS.\n541",
            "USURY LAWS.",
        ),
    ],
)
def test_exact_low_frequency_economics_page_heads_preserve_real_headings(
    processor_type: type, page_block: str, real_heading: str
) -> None:
    result = processor_type().process(
        f"sentence fragment\n\n{page_block}\ncontinues\n\n{real_heading}\nsection opening"
    )

    assert result.count(real_heading) == 1
    assert "continues" in result
    assert "section opening" in result
