import hashlib
import json

import pandas as pd
import pytest

from scripts.audit_principia_quality import (
    analyze_text,
    audit_rows,
    build_blind_sample_manifest,
    main,
)


def test_analyze_text_separates_hard_errors_from_review_heuristics():
    text = "\n".join(
        [
            "ＲＵＮＮＩＮＧ　ＨＥＡＤＥＲ",
            "42",
            "word-",
            "continuation",
            "proper-",
            "Title",
            "RUNNING   HEADER",
            "bad\ufffd\x01\ue000\u0378\ud800 soft\u00adhyphen firſt "
            "A0pha A1pha A|pha A5pha     !!!!!! ++++++ ?????",
            "Running Header",
            "ｄｕｐｌｉｃａｔｅ",
            "duplicate",
            "z" * 300,
            "y" * 301,
            "w" * 1000,
            "x" * 1001,
        ]
    )

    result = analyze_text(text)

    assert result["hard_errors"]["replacement_character"]["count"] == 1
    assert result["hard_errors"]["unexpected_control_character"]["count"] == 1
    assert result["hard_errors"]["private_use_character"]["count"] == 1
    assert result["hard_errors"]["soft_hyphen"]["count"] == 1
    assert result["hard_errors"]["unassigned_or_surrogate_character"]["count"] == 2
    suspicious_ocr = result["review_heuristics"]["suspicious_ocr_glyph"]
    assert suspicious_ocr["count"] == 5
    assert suspicious_ocr["breakdown"]["alpha_confusable_0_1_vertical_bar"] == 3
    assert suspicious_ocr["breakdown"]["additional_alpha_confusable_digit_5"] == 1
    assert result["review_heuristics"]["line_end_hyphenation"]["count"] == 1
    assert result["review_heuristics"]["isolated_page_number"]["count"] == 1
    assert result["review_heuristics"]["repeated_header_footer"]["count"] == 3
    assert result["review_heuristics"]["repeated_header_footer"]["candidate_pattern_count"] == 1
    assert result["review_heuristics"]["consecutive_duplicate_line"]["count"] == 1
    assert result["review_heuristics"]["consecutive_duplicate_line"]["excess_count"] == 1
    assert result["review_heuristics"]["consecutive_duplicate_line"]["run_count"] == 1
    assert result["review_heuristics"]["consecutive_duplicate_line"]["max_run_length"] == 2
    assert result["review_heuristics"]["global_recurrent_line"]["count"] == 3
    assert result["review_heuristics"]["global_recurrent_line"]["total_occurrences"] == 3
    assert result["review_heuristics"]["global_recurrent_line"]["excess_count"] == 2
    assert result["review_heuristics"]["global_recurrent_line"]["unique_pattern_count"] == 1
    assert result["review_heuristics"]["line_over_300_characters"]["count"] == 3
    assert result["review_heuristics"]["line_over_1000_characters"]["count"] == 1
    assert result["review_heuristics"]["pathological_whitespace"]["count"] > 0
    assert result["review_heuristics"]["pathological_punctuation"]["count"] == 12

    encoded = json.dumps(result)
    assert "Running Header" not in encoded
    assert "continuation" not in encoded


def test_audit_rows_matches_by_barcode_and_uses_weighted_retention():
    raw = [
        {"barcode": "book-b", "text": "second book\nline"},
        {"barcode": "book-a", "text": "alpha beta"},
    ]
    processed = [
        {"barcode": "book-a", "text": "alpha"},
        {"barcode": "book-b", "text": "second book\nline"},
    ]

    report = audit_rows(raw, processed)

    assert report["schema_version"] == "principia-quality-audit-v2"
    assert report["line_normalization"] == "NFKC-whitespace-collapse-casefold-v1"
    assert report["detector_parameters"]["ocr_alpha_confusable_characters"] == ["0", "1", "|"]
    assert report["detector_parameters"]["ocr_additional_digit_confusable_characters"] == ["5"]
    assert [book["barcode"] for book in report["books"]] == ["book-a", "book-b"]
    book_a = report["books"][0]
    assert book_a["raw_to_processed"]["retention"]["characters"] == {
        "reference_count": 10,
        "candidate_count": 5,
        "delta": -5,
        "loss_count": 5,
        "ratio": 0.5,
    }
    aggregate = report["aggregate"]["raw_to_processed"]["retention"]["characters"]
    assert aggregate["reference_count"] == 26
    assert aggregate["candidate_count"] == 21
    assert aggregate["ratio"] == 21 / 26


@pytest.mark.parametrize(
    ("processed", "message"),
    [
        ([{"barcode": "other", "text": "text"}], "barcode set differs"),
        (
            [
                {"barcode": "book", "text": "text"},
                {"barcode": "book", "text": "again"},
            ],
            "duplicate barcode",
        ),
    ],
)
def test_audit_rows_rejects_barcode_mismatch_and_duplicates(processed, message):
    raw = [{"barcode": "book", "text": "text"}]

    with pytest.raises(ValueError, match=message):
        audit_rows(raw, processed)


def test_baseline_diff_makes_candidate_content_loss_explicit():
    raw = [
        {"barcode": "changed", "text": "word-\nwrap"},
        {"barcode": "stable", "text": "unchanged"},
    ]
    baseline = [
        {"barcode": "stable", "text": "unchanged"},
        {"barcode": "changed", "text": "word-\nwrap"},
    ]
    candidate = [
        {"barcode": "changed", "text": "wordwrap"},
        {"barcode": "stable", "text": "unchanged"},
    ]

    report = audit_rows(raw, candidate, baseline_rows=baseline)
    diff = report["baseline_diff"]

    assert diff["books_with_content_loss"] == ["changed"]
    assert diff["aggregate"]["content_loss"] is True
    changed = diff["books"][0]
    assert changed["barcode"] == "changed"
    assert changed["changed"] is True
    assert changed["retention"]["characters"]["delta"] == -2
    assert changed["review_heuristic_count_delta"]["line_end_hyphenation"] == -1


def test_blind_samples_follow_exact_sha256_bins_and_are_stable():
    artifact_sha256 = "ab" * 32
    text = "zero\n\none\ntwo\n \nthree\nfour\nfive\nsix"
    rows = [{"barcode": "book-a", "text": text}]

    first = build_blind_sample_manifest(
        rows, processed_artifact_sha256=artifact_sha256, sample_windows=3
    )
    second = build_blind_sample_manifest(
        rows, processed_artifact_sha256=artifact_sha256, sample_windows=3
    )

    assert first == second
    assert first["processed_artifact_sha256"] == artifact_sha256
    assert first["sample_seed_sha256"] == artifact_sha256
    book = first["books"][0]
    assert book["nonempty_line_count"] == 7
    lines = text.split("\n")
    nonempty_indices = [index for index, line in enumerate(lines) if line.strip()]

    expected_ranges = [(0, 2), (2, 4), (4, 7)]
    assert [
        (
            sample["bin_nonempty_ordinal_start"],
            sample["bin_nonempty_ordinal_end_exclusive"],
        )
        for sample in book["samples"]
    ] == expected_ranges

    for bin_index, sample in enumerate(book["samples"]):
        bin_start, bin_end = expected_ranges[bin_index]
        digest = hashlib.sha256(
            artifact_sha256.encode("ascii")
            + b"\0"
            + b"book-a"
            + b"\0"
            + str(bin_index).encode("ascii")
        ).digest()
        expected_ordinal = bin_start + int.from_bytes(digest[:8], "big") % (bin_end - bin_start)
        expected_line_index = nonempty_indices[expected_ordinal]
        window_start = max(0, expected_line_index - 1)
        window_end = min(len(lines) - 1, expected_line_index + 1)
        expected_window_hash = hashlib.sha256(
            "\n".join(lines[window_start : window_end + 1]).encode("utf-8")
        ).hexdigest()

        assert sample["selected_nonempty_ordinal"] == expected_ordinal
        assert bin_start <= sample["selected_nonempty_ordinal"] < bin_end
        assert sample["physical_line_index"] == expected_line_index
        assert sample["window_sha256"] == expected_window_hash

    encoded = json.dumps(first)
    assert "zero" not in encoded
    assert "three" not in encoded


def test_blind_samples_reject_more_bins_than_nonempty_lines():
    with pytest.raises(ValueError, match="exceeds nonempty lines"):
        build_blind_sample_manifest(
            [{"barcode": "book", "text": "one\n\ntwo"}],
            processed_artifact_sha256="01" * 32,
            sample_windows=3,
        )


def test_blind_sample_seed_override_stabilizes_selection_across_artifact_drift():
    seed = "cd" * 32
    original = build_blind_sample_manifest(
        [{"barcode": "book", "text": "one\n\ntwo\nthree\nfour\nfive"}],
        processed_artifact_sha256="01" * 32,
        sample_windows=3,
        sample_seed_sha256=seed,
    )
    repaired = build_blind_sample_manifest(
        [{"barcode": "book", "text": "ONE\n\nTWO\nTHREE\nFOUR\nFIVE"}],
        processed_artifact_sha256="02" * 32,
        sample_windows=3,
        sample_seed_sha256=seed,
    )

    original_samples = original["books"][0]["samples"]
    repaired_samples = repaired["books"][0]["samples"]
    assert original["processed_artifact_sha256"] != repaired["processed_artifact_sha256"]
    assert original["sample_seed_sha256"] == repaired["sample_seed_sha256"] == seed
    assert [
        (sample["selected_nonempty_ordinal"], sample["physical_line_index"])
        for sample in original_samples
    ] == [
        (sample["selected_nonempty_ordinal"], sample["physical_line_index"])
        for sample in repaired_samples
    ]
    assert [sample["window_sha256"] for sample in original_samples] != [
        sample["window_sha256"] for sample in repaired_samples
    ]


def test_cli_rejects_sample_seed_without_sample_windows(capsys):
    with pytest.raises(SystemExit, match="2"):
        main(
            [
                "--raw",
                "unused-raw.parquet",
                "--processed",
                "unused-processed.parquet",
                "--sample-seed-sha256",
                "ab" * 32,
            ]
        )

    assert "--sample-seed-sha256 requires --sample-windows" in capsys.readouterr().err


def test_cli_reads_parquet_writes_json_and_does_not_mutate_inputs(tmp_path):
    raw_path = tmp_path / "raw.parquet"
    processed_path = tmp_path / "processed.parquet"
    output_path = tmp_path / "audit.json"
    raw_text = "harmless raw line\nsecond line"
    processed_text = "harmless processed line\nsecond line"
    pd.DataFrame([{"barcode": "book", "text": raw_text}]).to_parquet(raw_path, index=False)
    pd.DataFrame([{"barcode": "book", "text": processed_text}]).to_parquet(
        processed_path, index=False
    )
    raw_before = raw_path.read_bytes()
    processed_before = processed_path.read_bytes()

    assert (
        main(
            [
                "--raw",
                str(raw_path),
                "--processed",
                str(processed_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["inputs"]["raw"]["sha256"] == hashlib.sha256(raw_before).hexdigest()
    assert report["inputs"]["processed"]["sha256"] == hashlib.sha256(processed_before).hexdigest()
    assert "blind_samples" not in report
    assert raw_path.read_bytes() == raw_before
    assert processed_path.read_bytes() == processed_before
    encoded = output_path.read_text(encoding="utf-8")
    assert raw_text not in encoded
    assert processed_text not in encoded
