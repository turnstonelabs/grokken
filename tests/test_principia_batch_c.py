"""Regressions for the Phase 0 quality audit, Principia batch C."""

import pytest

from grokken.books.principia.international_law_davis_1903 import (
    InternationalLawDavis1903,
)
from grokken.books.principia.international_law_woolsey import InternationalLawWoolsey
from grokken.books.principia.logical_theory_dewey import LogicalTheory
from grokken.books.principia.middle_ages_emerton import MiddleAges
from grokken.books.principia.natural_philosophy_comstock import NaturalPhilosophy
from grokken.books.principia.parliamentary_practice_cushing import (
    _CANONICAL_CONTENTS,
    _CANONICAL_TITLE,
    ParliamentaryPractice,
)
from grokken.books.principia.pathologic_histology_mallory import PathologicHistology
from grokken.books.principia.poetical_works_whittier import WhittierPoetry


@pytest.mark.parametrize(
    ("processor_type", "running_header"),
    [
        (InternationalLawDavis1903, "THE ELEMENTS OF INTERNATIONAL LAW"),
        (InternationalLawWoolsey, "BELLIGERENTS AND NEUTRALS."),
        (LogicalTheory, "STUDIES IN LOGICAL THEORY"),
        (MiddleAges, "CHARLEMAGNE KING OF THE FRANKS."),
        (NaturalPhilosophy, "ASTRONOMY."),
        (ParliamentaryPractice, "Parliamentary Practice."),
        (PathologicHistology, "PATHOLOGIC HISTOLOGY"),
        (WhittierPoetry, "VOICES OF FREEDOM."),
    ],
)
def test_numbered_running_headers_are_removed_but_real_headings_remain(
    processor_type: type, running_header: str
) -> None:
    text = (
        f"opening text\n42\n{running_header}\ncontinued text\n"
        f"{running_header}\n43\nmore text\n\n{running_header}\nsection opening"
    )

    result = processor_type().process(text)

    assert result.count(running_header) == 1
    assert "opening text" in result
    assert "continued text" in result
    assert "more text" in result
    assert "section opening" in result


def test_book_specific_layout_guards_preserve_domain_content() -> None:
    assert "§ 42." in InternationalLawDavis1903().process("Treaty citation, vol. II, § 42.")
    assert "42 | 7" in NaturalPhilosophy().process("Observed values\n42 | 7\nEnd")
    assert "blood-\nstained" in WhittierPoetry().process("A blood-\nstained field")


@pytest.mark.parametrize(
    "processor_type",
    [
        InternationalLawDavis1903,
        InternationalLawWoolsey,
        LogicalTheory,
        MiddleAges,
        NaturalPhilosophy,
        ParliamentaryPractice,
        PathologicHistology,
        WhittierPoetry,
    ],
)
def test_unpaired_numbers_and_ocr_sensitive_content_are_preserved(processor_type: type) -> None:
    text = "17\n+\n=\n*\n†\n......\nsooooo\n1x1x1\na0b"

    assert processor_type().process(text) == text


@pytest.mark.parametrize(
    "processor_type",
    [
        InternationalLawDavis1903,
        InternationalLawWoolsey,
        LogicalTheory,
        MiddleAges,
        NaturalPhilosophy,
        ParliamentaryPractice,
        PathologicHistology,
        WhittierPoetry,
    ],
)
def test_book_specific_cleanup_collapses_blank_runs_and_trims(processor_type: type) -> None:
    assert processor_type().process("\nstart\n\n\n\nend\n\n") == "start\n\nend"


def test_davis_citation_and_treaty_ocr_repairs_are_exact() -> None:
    text = (
        "Twiss, $$ 98-120.\n$ 92.\nCase of the Exchange,7 Cranch.\n"
        "pp.99, 100.\nSweden and Norway, May 56, 1869.\nA fine of $600.\n"
        "* wwwwwww\nsooooo"
    )

    result = InternationalLawDavis1903().process(text)

    assert "Twiss, §§ 98-120." in result
    assert "§ 92." in result
    assert "Exchange, 7 Cranch" in result
    assert "pp. 99, 100" in result
    assert "May 26, 1869" in result
    assert "$600" in result
    assert "wwwwwww" not in result
    assert "sooooo" in result


def test_woolsey_standalone_section_ocr_preserves_currency() -> None:
    result = InternationalLawWoolsey().process(
        "$148.\nAn award of $15,500,000 in gold.\nmedi-\næval Latin\ndélib-\nérations ultérieures"
    )

    assert result == (
        "§148.\nAn award of $15,500,000 in gold.\nmediæval Latin\ndélibérations ultérieures"
    )


def test_dewey_word_boundary_repair() -> None:
    result = LogicalTheory().process("it matters notthat shall serve")

    assert result == "it matters not that shall serve"


def test_middle_ages_local_ocr_repairs_preserve_map_text() -> None:
    result = MiddleAges().process("A nátive duke\ntho borders of Italy\nROMA 42")

    assert result == "A native duke\nthe borders of Italy\nROMA 42"


def test_natural_philosophy_local_crop_repairs() -> None:
    text = (
        "in Washing\nton College\nalong. Bu\non making\nThe re\naction of the atmosphere\n"
        "the bel\nlows\nmoved at alt, for\n15lbs..\nsec_Chemistry\nantartic circle\n"
        "non-conduct\nors"
    )

    result = NaturalPhilosophy().process(text)

    assert result == (
        "in Washington College\nalong. But\non making\nThe reaction of the atmosphere\n"
        "the bellows\nmoved at all, for\n15 lbs.\nsee Chemistry\nantarctic circle\n"
        "non-conductors"
    )


@pytest.mark.parametrize(
    ("header", "split_text", "continuation", "expected"),
    [
        ("Amendment of Amendments.", "by rea-", "son", "by reason"),
        ("Reconsideration.", "and inconven-", "ience", "and inconvenience"),
    ],
)
def test_cushing_rejoins_words_split_by_verified_page_heads(
    header: str, split_text: str, continuation: str, expected: str
) -> None:
    result = ParliamentaryPractice().process(f"{split_text}\n{header}\n103\n{continuation}")

    assert result == expected


def test_cushing_local_spelling_repair() -> None:
    result = ParliamentaryPractice().process("begining with the largest")

    assert result == "beginning with the largest"


@pytest.mark.parametrize(
    "broken",
    [
        "ascer-\ntaining",
        "be-\nyond",
        "exten-\nsions",
        "perform-\nance",
        "pro-\nvide",
        "num-\nbered",
        "ap-\nprobation",
        "allu-\nsion",
        "sugges-\ntions",
        "appro-\npriately",
        "improp-\nerly",
        "re-\ncede",
        "com-\nprehends",
        "com-\nmence",
        "dis-\ntributed",
        "in-\ndications",
        "in-\ncompatibility",
        "Dele-\ngates",
        "satis-\nfactorily",
        "actu-\nally",
        "subsist-\ning",
        "ex-\namples",
        "ex-\nample",
        "sit-\nuation",
        "adjourn-\nment",
        "independ-\nently",
        "evi-\ndently",
        "direct-\ning",
        "in-\nsert",
        "consist-\ning",
        "compara-\ntively",
        "sepa-\nrating",
        "repro-\nbated",
        "mo-\ntions",
        "person-\nality",
        "perempto-\nrily",
        "equiva-\nlents",
        "un-\nderstandingly",
        "de-\ncline",
        "pro-\nceeding",
        "har-\nmony",
        "diffi-\ndent",
        "neces-\nsary",
    ],
)
def test_cushing_confirmed_single_occurrence_wraps_are_joined(broken: str) -> None:
    assert ParliamentaryPractice().process(broken) == broken.replace("-\n", "")


def test_cushing_blind_window_repairs_are_exact() -> None:
    text = (
        "The terms \" general consent,' as used in\n"
        "parliamentary practice, denote the unanimous.\nopinion\n\n"
        "it is a compendious mode of\n\nDivision of a Question.\n61\n"
        "amendment to divide the motion\n\n"
        "The accept-\n\nance by the mover\n\n"
        "are, fur-\n\nAppointment of Committees. 155\n·\nther instructed\n\n"
        'some other time is mentioned, as 66 to-mor-\nor Monday," and that time is fixed\n'
        "by general consent. But, when it is not the\n"
        "general sense of the assembly to receive the\n"
        "report at the time, it is better to agree upon\n"
        'and fix the time by a motion and question.\nrow\n""\n66\n\n'
        "178\nParliamentary Practice.\nCONCLUDING REMARKS."
    )

    result = ParliamentaryPractice().process(text)

    assert result == (
        'The terms "general consent," as used in\n'
        "parliamentary practice, denote the unanimous\nopinion\n\n"
        "it is a compendious mode of\namendment to divide the motion\n\n"
        "The acceptance by the mover\n\n"
        "are, further instructed\n\n"
        'some other time is mentioned, as "to-morrow"\nor "Monday," and that time is fixed\n'
        "by general consent. But, when it is not the\n"
        "general sense of the assembly to receive the\n"
        "report at the time, it is better to agree upon\n"
        "and fix the time by a motion and question.\n\nCONCLUDING REMARKS."
    )


def test_cushing_repositions_page_footnote_out_of_split_word() -> None:
    text = (
        "the motion to adjourn. In the absence, how-\n"
        "1 In legislative bodies, it is usual to provide that certain\n"
        "questions, as, for example, to adjourn, to lie on the table, for the\n"
        "previous question, or as to the order of business, shall be decided\n"
        "without debate.\n\n"
        "ever, of a special rule restricting the right of\n"
        "debate in reference to some particular subject,\n"
        "every question, with the exception perhaps of\n"
        "those which require unanimity, that may be\n"
        "moved, may be debated. In both houses of\n"
        "parliament, important debates have frequently\n"
        "taken place on motions, as, for example, to\n"
        "adjourn, which in the legislative assemblies\n"
        "of this country would not generally be considered debatable."
    )

    result = ParliamentaryPractice().process(text)

    assert "absence, however, of a special rule" in result
    assert result.endswith(
        "1 In legislative bodies, it is usual to provide that certain\n"
        "questions, as, for example, to adjourn, to lie on the table, for the\n"
        "previous question, or as to the order of business, shall be decided\n"
        "without debate."
    )


@pytest.mark.parametrize(
    "header",
    [
        "Parliamentary Practice.",
        "Table of Contents.",
        "Organization.",
        "Returns and Elections.",
        "Rules of Proceeding.",
        "Making of Propositions.",
        "Rules and Orders.",
        "Principle of Decision.",
        "Of the Officers.",
        "Presiding Officer.",
        "Secretary or Clerk.",
        "Deportment of Members.",
        "Breaches of Decorum.",
        "Introduction of Business.",
        "Obtaining the Floor.",
        "Presenting a Petition.",
        "Making a Motion.",
        "Motion Made and Stated.",
        "Of Motions in General.",
        "Subsidiary Motions.",
        "Index.",
        "Amendments.",
        "Amendments..",
        "Indefinite Postponement.",
        "Of Motions to Postpone.",
        "Of Motions to Commit.",
        "Proceedings of Committees.",
        "Of the Question.",
        "Order of Proceeding.",
        "Previous Question.",
        "Committee of the Whole.",
        "Commitment.",
        "Amendment of Amendments.",
        "Reconsideration.",
        "Division of a Question.",
        "Filling Blanks.",
        "Addition, Separation.",
        "Adjournment.",
        "Orders of the Day.",
        "Incidental Questions.",
        "Questions of Order.",
        "Reading Papers.",
        "Subsidiary Questions.",
        "Amendment.",
        "Order in Debate.",
        "Matter in Speaking.",
        "Times of Speaking.",
        "Stopping Debate.",
        "Decorum in Debate.",
        "Disorderly Words.",
        "Committees.",
        "Appointment of Committees.",
        "Organization of Committees.",
        "Concluding Remarks.",
    ],
)
def test_cushing_removes_every_observed_running_head_only_with_folio(header: str) -> None:
    result = ParliamentaryPractice().process(
        f"left page\n\n77\n{header}\nright page\n\n{header}\n78\nnext page"
    )

    assert result == "left page\nright page\nnext page"
    assert ParliamentaryPractice().process(f"chapter text\n\n{header}") == (
        f"chapter text\n\n{header}"
    )


@pytest.mark.parametrize(
    "inline_header",
    [
        "Order and Succession of Questions. 87",
        "Appointment of Committees. 155",
        "Organization of Committees. 159",
        "Committee of the Whole. 177",
    ],
)
def test_cushing_removes_verified_inline_running_heads(inline_header: str) -> None:
    assert ParliamentaryPractice().process(f"before\n\n{inline_header}\nafter") == ("before\nafter")


def test_cushing_canonical_front_matter_and_contents_retain_source_structure() -> None:
    assert _CANONICAL_TITLE.startswith("MANUAL OF PARLIAMENTARY PRACTICE.\nRULES")
    assert "DELIBERATIVE ASSEMBLIES.\nBY\nLUTHER S. CUSHING." in _CANONICAL_TITLE
    assert "CHAPTER X. — OF THE ORDER AND SUCCESSION OF QUESTIONS — 134 to 187" in (
        _CANONICAL_CONTENTS
    )
    assert "SECT. VIII. Amendments by striking out and inserting — 122 to 127" in (
        _CANONICAL_CONTENTS
    )
    assert _CANONICAL_CONTENTS.endswith("ADDITIONS AND CORRECTIONS — 316 to 340\n")
    assert not {"•", "·"} & set(_CANONICAL_CONTENTS)


@pytest.mark.parametrize(
    ("broken", "repaired"),
    [
        (
            "those which are of general application,\nwhich it specially adopts",
            "those which are of general application, or\nwhich it specially adopts",
        ),
        (
            "effected by means of a mot that the matter",
            "effected by means of a motion that the matter",
        ),
        ("to which it relates to signif his consent", "to which it relates to signify his consent"),
        ("to insert C E, or\nDE, or C D E.", "to insert C E, or\nD E, or C D E."),
        ("120, There is no precedence", "120. There is no precedence"),
        (
            "made to express more clearly\nexpress.\nand definitely the sense which it is "
            "intended to\nHence",
            "made to express more clearly\nand definitely the sense which it is intended "
            "to\nexpress. Hence",
        ),
        (
            "but, if decided the other way, leave\nbefore.\nas\nSECTION I.",
            "but, if decided the other way, leave it as\nbefore.\nSECTION I.",
        ),
        ("The same result may\nreached more simply", "The same result may be\nreached more simply"),
        ("previous question or for posponement", "previous question or for postponement"),
        (
            "or series of resolutions, or other paper, has å\npreamble",
            "or series of resolutions, or other paper, has a\npreamble",
        ),
        (
            "of an assembly are guilty of this piece of\nmanners",
            "of an assembly are guilty of this piece of ill\nmanners",
        ),
        ("till the membe has finished", "till the member has finished"),
        ("Shall the main question he now put?", "Shall the main question be now put?"),
        (
            "258. is usual in all deliberative assemblies",
            "258. It is usual in all deliberative assemblies",
        ),
        ("compatible with th forms", "compatible with the forms"),
        ("this being reserved\nA NA MA\nfor the close", "this being reserved\nfor the close"),
        (
            "either in reason or parlimentary\nusage",
            "either in reason or parliamentary\nusage",
        ),
        ("interference, to\ncheek offensive", "interference, to\ncheck offensive"),
        ("obstruct the ex-\npression", "obstruct the expression"),
        (
            "when before the assembly, none other can bẻ",
            "when before the assembly, none other can be",
        ),
        ("no debate upoù, allowed", "no debate upon, allowed"),
        ("the previo question, 179.", "the previous question, 179."),
        ("TRANSPO-\nSITION.", "TRANSPOSITION."),
        ("THE EX-\nPRESSION", "THE EXPRESSION"),
    ],
)
def test_cushing_source_confirmed_text_repairs_are_exact(broken: str, repaired: str) -> None:
    result = ParliamentaryPractice().post_process(broken)

    assert result == repaired


@pytest.mark.parametrize(
    ("broken", "repaired"),
    [
        ('unanimous.\n""\n22.', "unanimous.\n22."),
        (
            "elected by a plurality. — ED.]\n-\nSECTION I.",
            "elected by a plurality. — ED.]\nSECTION I.",
        ),
        (
            "contrary not only to the laws of decency, but\n———\nto the fundamental",
            "contrary not only to the laws of decency, but\nto the fundamental",
        ),
        (
            "for that purpose. But\n\n62\n·\nParliamentary Practice.\nthis is a mistake",
            "for that purpose. But\nthis is a mistake",
        ),
        (
            "rejected without a division.¹\n-\n1 This mode",
            "rejected without a division.¹\n1 This mode",
        ),
        (
            "wholly different tenor.\n,\nIn some legislative assemblies",
            "wholly different tenor.\nIn some legislative assemblies",
        ),
        (
            "considered and treated accordingly.\n—\n177.",
            "considered and treated accordingly.\n177.",
        ),
        ('preamble\n"\nor title', "preamble\nor title"),
        (
            "it is the duty of the presiding officer to propose\n#\nit to the assembly",
            "it is the duty of the presiding officer to propose\nit to the assembly",
        ),
        ('"That vote is doubted."\n1\n239.', '"That vote is doubted."\n239.'),
    ],
)
def test_cushing_verified_page_edge_noise_is_removed_without_blanket_rules(
    broken: str, repaired: str
) -> None:
    assert ParliamentaryPractice().post_process(broken) == repaired


def test_cushing_displaced_section_word_is_restored_to_its_sentence() -> None:
    text = (
        "SECT. III. ADDITION, SEPARATION, TRANSPO-\nSITION.\none.\n88. When the "
        "matters contained in two separate propositions might be better put into one,\n"
        "instructions to incorporate them together in\n89. So, on the other hand"
    )

    result = ParliamentaryPractice().post_process(text)

    assert "TRANSPOSITION.\n88." in result
    assert "incorporate them together in one.\n89." in result
    assert "TRANSPOSITION.\none." not in result


def test_mallory_local_word_boundary_repairs() -> None:
    text = (
        "tissues showing lesions.\nwhich I had\nvarious in-\n\nfluences\n"
        "smooth musclecells\nsolitary lymphnodules\nGiantcells"
    )

    result = PathologicHistology().process(text)

    assert result == (
        "tissues showing lesions\nwhich I had\nvarious influences\n"
        "smooth muscle-cells\nsolitary lymph-nodules\nGiant-cells"
    )


def test_mallory_repositions_caption_out_of_split_word() -> None:
    text = (
        "disappear. Some-\n\nFig. 390.-Pancreas. Concretions in dilated glands.\ntimes the hyaline"
    )

    result = PathologicHistology().process(text)

    assert result == (
        "disappear.\n\nFig. 390.-Pancreas. Concretions in dilated glands.\n\nSometimes the hyaline"
    )


def test_mallory_repositions_confirmed_fig_132_caption_without_losing_it() -> None:
    source = (
        "Regenerative proliferation of fibroblasts is fairly active. Exu-\n\n"
        "Fig. 132. Syphilis. Primary lesion. Two mitoses in wall of blood-vessel. M.\n"
        "dation and regeneration take place in the corium."
    )

    result = PathologicHistology().process(source)

    assert result == (
        "Regenerative proliferation of fibroblasts is fairly active.\n\n"
        "Fig. 132. Syphilis. Primary lesion. Two mitoses in wall of blood-vessel. M.\n\n"
        "Exudation and regeneration take place in the corium."
    )


def test_mallory_repositions_confirmed_fig_162_caption_after_contiguous_prose() -> None:
    source = (
        "days it curls up in its characteristic spiral attitude, becomes ap-\n\n"
        "Fig. 162.-Trichiniasis. Part of a muscle-fiber showing portions necrotic and\n"
        "other portions beginning to regenerate.\n"
        "parently innocuous, and may persist in this condition for years\n"
        "(twenty or more) until death of its host and ingestion of the infected muscle by "
        "another host sets it free to continue the cycle of\n"
        "development."
    )

    result = PathologicHistology().process(source)

    assert result == (
        "days it curls up in its characteristic spiral attitude, becomes apparently "
        "innocuous, and may persist in this condition for years\n"
        "(twenty or more) until death of its host and ingestion of the infected muscle by "
        "another host sets it free to continue the cycle of\n"
        "development.\n\n"
        "Fig. 162.-Trichiniasis. Part of a muscle-fiber showing portions necrotic and\n"
        "other portions beginning to regenerate."
    )


def test_mallory_repairs_only_contextual_spurious_period() -> None:
    source = "the lesions cannot be told.\napart and the bacilli\nA complete sentence.\nApart"

    result = PathologicHistology().process(source)

    assert result == (
        "the lesions cannot be told\napart and the bacilli\nA complete sentence.\nApart"
    )


def test_mallory_repairs_refreshed_sample_without_broad_punctuation_changes() -> None:
    source = (
        "the cells of the trans-\n\nplanted bone always die\n"
        "separated by thin non-vascular, walls\n"
        "A different, grammatical comma remains."
    )

    result = PathologicHistology().process(source)

    assert result == (
        "the cells of the transplanted bone always die\n"
        "separated by thin non-vascular walls\n"
        "A different, grammatical comma remains."
    )


@pytest.mark.parametrize(
    "broken",
    [
        "obliga-\ntions",
        "pre-\ndominating",
        "disen-\ntangle",
        "constrict-\ning",
        "dissem-\ninated",
        "pig-\nmentosa",
        "pete-\nchial",
        "bath-\ning",
        "hemo-\nlyze",
        "preserv-\natives",
        "bacterio-\nlogically",
        "inoculat-\ning",
        "cur-\nrents",
        "ele-\nmentary",
        "Leva-\nditi",
        "unsatis-\nfactory",
        "acqui-\nsition",
        "micro-\nnucleus",
        "fertiliza-\ntion",
        "environ-\nments",
        "devia-\ntions",
        "deli-\ncacy",
        "har-\nmonize",
        "un-\nsatisfactory",
        "improve-\nments",
        "embryo-\nblastoma",
        "young-\nest",
        "osteo-\nsarcomas",
        "intramuscu-\nlarly",
        "in-\nfantry",
        "dis-\ncover",
        "undeter-\nmined",
        "unde-\ntermined",
        "elabo-\nrately",
        "nephro-\ngenic",
        "ento-\nderm",
        "trans-\nplantations",
        "in-\ncompetence",
        "ante-\ncedent",
        "disadvanta-\ngeous",
        "bronchi-\nectases",
        "per-\nforate",
        "under-\nlies",
        "back-\nground",
        "hexamethyl-\nenamine",
        "Phos-\nphates",
        "cas-\ntrated",
        "tortu-\nous",
        "symmet-\nrical",
        "ex-\npanded",
        "child-\nhood",
        "sim-\nplifies",
        "de-\nmand",
        "favor-\ning",
    ],
)
def test_mallory_confirmed_single_occurrence_wraps_are_joined(broken: str) -> None:
    assert PathologicHistology().process(broken) == broken.replace("-\n", "")


@pytest.mark.parametrize(
    "broken",
    [
        "type-\nwriting",
        "over-\nuse",
        "non-\ntoxic",
        "normal-\nlooking",
        "pseudo-\nmuscular",
        "grape-\nsugar",
        "twenty-\neighth",
        "pearl-\nlike",
        "Myxomatous-\nlike",
        "muscle-\nbundles",
        "heart-\nfibers",
        "motor-\nexciting",
        "endothelial-\ncell",
        "fibrino-\npurulent",
        "colon-\nlike",
        "mucus-\nsecreting",
        "full-\nfledged",
        "osteochondro-\nfibrosarcoma",
    ],
)
def test_mallory_confirmed_lexical_compounds_retain_hyphens(broken: str) -> None:
    assert PathologicHistology().process(broken) == broken.replace("\n", "")


def test_mallory_blind_window_and_cyrillic_ocr_repairs_are_exact() -> None:
    text = (
        "nature goes ahout it in the same way.\n"
        "Somtimes the organisms remain within the vessels.\n"
        "The epithelium but little differentiated. \u041e\u0441\u0441\u0430-\n"
        "sionally they are destroyed.\n"
        "where-\never it occurs.\n"
        "In typhoid fever focal lesions like those in the liver and com-\n39\n\n"
        "posed of phagocytic endothelial leukocytes"
    )

    result = PathologicHistology().process(text)

    assert result == (
        "nature goes about it in the same way.\n"
        "Sometimes the organisms remain within the vessels.\n"
        "The epithelium but little differentiated. Occasionally they are destroyed.\n"
        "wherever it occurs.\n"
        "In typhoid fever focal lesions like those in the liver and composed of "
        "phagocytic endothelial leukocytes"
    )


def test_mallory_reconstructs_confirmed_interleaved_table_row() -> None:
    text = (
        "6. Leiomyoblast (smooth muscle- Leiomyoblastoma (leiomyoma, leio-\n"
        "cell).\n"
        "7. Endothelioblast\n"
        "15. Epithelioblast (epithelial cell).\n"
        "myosarcoma).\n"
        "Endothelioblastoma."
    )

    result = PathologicHistology().process(text)

    assert result == (
        "6. Leiomyoblast (smooth muscle-cell).\n"
        "Leiomyoblastoma (leiomyoma, leiomyosarcoma).\n"
        "7. Endothelioblast\n"
        "15. Epithelioblast (epithelial cell).\n"
        "Endothelioblastoma."
    )


@pytest.mark.parametrize("processor_type", [ParliamentaryPractice, PathologicHistology])
def test_gold_wrap_repairs_do_not_generalize_to_unlisted_compounds(processor_type: type) -> None:
    text = "risk-\ntaking\n66\n+\n......"

    assert processor_type().process(text) == text


def test_whittier_only_joins_confirmed_print_wraps() -> None:
    text = (
        "autumn's ris-\ning blast\nsmothered thun-\nder,\nloved and cher-\nished\n"
        "a hid-\nden fire\n"
        "chil-\ndren yet\nblood-\nstained"
    )

    result = WhittierPoetry().process(text)

    assert result == (
        "autumn's rising blast\nsmothered thunder,\nloved and cherished\n"
        "a hidden fire\nchildren yet\nblood-\nstained"
    )
