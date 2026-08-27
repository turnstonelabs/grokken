"""Focused regressions for the two Principia validation books."""

from grokken.books.principia.federalist import Federalist
from grokken.books.principia.psychology_james import PrinciplesPsychology


def test_psychology_preserves_ligatures_and_rejoins_their_line_breaks():
    text = (
        "CHAPTER XVII.\n"
        "The patient was an-\næsthetic and interested in higher\næsthetic feeling.\n"
        "THE END.\n"
    )

    result = PrinciplesPsychology().post_process(text)

    assert "anæsthetic" in result
    assert "higher æsthetic" in result
    assert "an-\næsthetic" not in result
    assert "higher\næsthetic" not in result


def test_psychology_preserves_decorated_chapter_titles():
    text = (
        "CHAPTER XIX.\n"
        "THE PERCEPTION OF THINGS.'\n"
        "CHAPTER XX.\n"
        "THE PERCEPTION OF SPACE.*\n"
        "THE END.\n"
    )

    result = PrinciplesPsychology().post_process(text)

    assert "THE PERCEPTION OF THINGS.'" in result
    assert "THE PERCEPTION OF SPACE.*" in result


def test_psychology_removes_evidenced_page_headers_and_scan_noise():
    text = (
        "CHAPTER XVII.\n"
        "First clause\n\n446\n\nPSYCHOLOGY\ncontinued clause.\n"
        'A citation in vol. ш., a favμa, and " а bird in the hand."\n'
        "с\nFIG. 68.\n"
        "肇\nՂԱՏ.\nि\n་\n"
        "THE END.\n"
    )

    result = PrinciplesPsychology().post_process(text)

    assert "446" not in result
    assert "PSYCHOLOGY" not in result
    assert "vol. III." in result
    assert "θαῦμα" in result
    assert '" a bird in the hand' in result
    assert "c\nFIG. 68." in result
    assert "肇" not in result
    assert "ՂԱՏ" not in result
    assert "\n.\n" not in result
    assert "ि" not in result
    assert "་" not in result


def test_psychology_preserves_unconfirmed_symbols_and_character_runs():
    result = PrinciplesPsychology().process(
        "Wait.....\n*\nAAAAAA\nᎠ\nι\n十\nλόγος remains Greek.\n66 6\nmatrix 1x1x1"
    )

    assert "Wait....." in result
    assert "\n*\n" in result
    assert "AAAAAA" in result
    assert "Ꭰ" in result
    assert "ι" in result
    assert "十" in result
    assert "λόγος remains Greek." in result
    assert "66 6" in result
    assert "1x1x1" in result


def test_psychology_preserves_reference_attested_compounds():
    text = (
        "CHAPTER XVII.\n"
        "The word afterimage also occurs in OCR.\n"
        "This edition prints an after-\nimage and a by-\n\ngone memory.\n"
        "THE END.\n"
    )

    result = PrinciplesPsychology().process(text)

    assert "after-image" in result
    assert "by-gone" in result


def test_psychology_repairs_verified_local_ocr_and_page_splits():
    text = (
        "CHAPTER XVII.\n"
        "A passage on Erkenntnisstheoric.\n\n"
        "(P. 266.)\n6\nThe commonplace doctrine and that of predicate\n"
        "1\n1\n1\n1\n\nto subject may be one.\n\n"
        "which we proceed in turn to consider.\n6\nPugnacity; anger; resentment.\n\n"
        "Outlines of Psychology, p. 593.\n4\n\nonly thing to do.\n\n"
        "validity of his own.. Every visual sensation\n\n"
        "a facewith clearness\n\n"
        "dinary parlance hallucination\n\n"
        "local patho logical activity\n\n"
        "then, if the pain seem small\n\n"
        "association by similarity. I ca find examples.\n\n"
        "guage is assuredly important.\n\n"
        "preposterous inertia and negi ativeness\n\n"
        "A prior sentence.\ncoup that we find an answer\n\n"
        "A prior sentence.\nof them have no single sensation\n\n"
        "and the mechanical\n\nphilosophy is only a way\n"
        "THE END.\n"
    )

    result = PrinciplesPsychology().post_process(text)

    assert "Erkenntnisstheorie" in result
    assert "(P. 266.)\n\nThe commonplace" in result
    assert "that of predicate to subject" in result
    assert "consider.\n\nPugnacity" in result
    assert "p. 593.\n\nonly thing" in result
    assert "own. Every visual" in result
    assert "face with clearness" in result
    assert "In ordinary parlance" in result
    assert "local pathological activity" in result
    assert "What wonder, then, if the pain seem" in result
    assert "I can find examples" in result
    assert "language is assuredly" in result
    assert "inertia and negativeness" in result
    assert "après coup that we find" in result
    assert "Let some of them have no single sensation" in result
    assert "the mechanical philosophy is only" in result


def test_federalist_repairs_page_id_word_splices():
    text = (
        "INTRODUCTION.\n"
        'General HAMILxxxii\n\nTON wrote an exxxxvi\n\n"pression.\n'
        'Mr. MADIlxxxiii\n"SON noted a discxxxiii agreement and good '
        "becxxxiv\n\nEssay. Page havior.\n"
        "END OF VOL. I.\n"
    )

    result = Federalist().post_process(text)

    assert "General HAMILTON wrote an expression." in result
    assert "Mr. MADISON noted a disagreement and good behavior." in result


def test_federalist_repairs_source_preserving_page_id_seams():
    text = (
        "INTRODUCTION.\n"
        'General HAMIL-\n\nTON wrote an ex-\n\n"pression.\n'
        'Mr. MADI-\n\n-\n"SON noted a dis-\n\nagreement and good '
        "bec-\n\nEssay. Page\nhavior.\n"
        "END OF VOL. I.\n"
    )

    result = Federalist().post_process(text)

    assert "General HAMILTON wrote an expression." in result
    assert "Mr. MADISON noted a disagreement and good behavior." in result


def test_federalist_does_not_guess_across_unverified_blank_gaps():
    text = (
        "INTRODUCTION.\n"
        "Corrupt tokens arcontained and interas occur elsewhere.\n"
        "A corrupt boundary leaves ar-\n\ncontained unresolved.\n"
        "Another leaves inter-\n\nas mixed text.\n"
        "END OF VOL. I.\n"
    )

    result = Federalist().post_process(text)

    assert "ar-\n\ncontained" in result
    assert "inter-\n\nas mixed" in result
    assert result.count("arcontained") == 1
    assert result.count("interas") == 1


def test_federalist_rejoins_attested_page_gap_words():
    text = (
        "INTRODUCTION.\n"
        "The principles are independently attested.\n"
        "These prin-\n\nciples rejoin after verified furniture removal.\n"
        "END OF VOL. I.\n"
    )

    result = Federalist().post_process(text)

    assert "These principles rejoin" in result


def test_federalist_repairs_verified_residual_wraps_and_quote_furniture():
    text = (
        "INTRODUCTION.\n"
        "Foder-\n\nal courts were pro-\n\nfessing views both trouble-\nsome and "
        "trouble-\n\nsome.\n"
        "The geome-\n\ntricians excluded in-\n\nquisitors under inter-\n\ndicts "
        "against de-\n\ngeneracy.\n"
        '"The free inhabitants, pau-\n\npers excepted,\n'
        '"shall be entitled to privileges in the Fod-\neral system.\n'
        "END OF VOL. I.\n"
    )

    result = Federalist().post_process(text)

    for joined in (
        "Foderal",
        "professing",
        "troublesome",
        "geometricians",
        "paupers",
        "interdicts",
        "degeneracy",
        "inquisitors",
    ):
        assert joined in result
    assert "paupers excepted, shall be entitled" in result
    assert '\n"shall be entitled' not in result


def test_federalist_preserves_attested_compound_hyphenation():
    text = (
        "INTRODUCTION.\n"
        "A well-known example remains well-\nknown in this edition.\n"
        "END OF VOL. I.\n"
    )

    result = Federalist().process(text)

    assert "well-known" in result
    assert "wellknown" not in result


def test_federalist_rejoins_repeated_quote_line_furniture():
    text = (
        "INTRODUCTION.\n"
        '"The maintenance of his opinions, if erro-\n'
        " neous, can lessen his char-\n"
        '"acter.\n'
        '"A second printed line begins here\n'
        '"and continues here.\n\n'
        '"A third printed line has an unquoted\n'
        "continuation before the next printed line\n"
        '"and must still reach the quote cleanup.\n\n'
        "A new paragraph.\n"
        "END OF VOL. I.\n"
    )

    result = Federalist().post_process(text)

    assert "erroneous" in result
    assert "character" in result
    assert "character. A second printed line begins here and continues here." in result
    assert (
        "A third printed line has an unquoted continuation before the next printed line "
        "and must still reach the quote cleanup."
    ) in result
    assert "cleanup.\n\nA new paragraph" in result


def test_federalist_preserves_unconfirmed_symbols_and_character_runs():
    text = "INTRODUCTION.\nWait.....\n*\nNOOOOO\nmatrix 1x1x1\nEND OF VOL. I.\n"

    result = Federalist().process(text)

    assert "Wait..." in result
    assert "\n*\n" in result
    assert "NOOOOO" in result
    assert "1x1x1" in result
