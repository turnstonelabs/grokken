import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import pytest

from scripts.build_principia_qualification import (
    EXPECTED_AUDIT_SHA256,
    EXPECTED_CANDIDATE_SHA256,
    MANUAL_CATEGORIES,
    build_qualification,
    compute_token_counts,
    render_json,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ENV = os.environ.get("PRINCIPIA_QUALIFIED_CANDIDATE")
CANDIDATE = Path(CANDIDATE_ENV) if CANDIDATE_ENV else None
AUDIT = ROOT / "experiments/audits/principia-34-candidate-quality-20260826-r8.json"
QUALIFICATION = ROOT / "experiments/audits/principia-34-qualification-20260826.json"


@pytest.fixture(scope="module")
def qualification():
    return json.loads(QUALIFICATION.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def audit():
    return json.loads(AUDIT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def candidate_records():
    if CANDIDATE is None or not CANDIDATE.exists():
        pytest.skip("set PRINCIPIA_QUALIFIED_CANDIDATE to run external Parquet integration checks")
    import pandas as pd

    return pd.read_parquet(CANDIDATE).to_dict(orient="records")


def test_manifest_is_canonical_sorted_json(qualification):
    assert render_json(qualification) == QUALIFICATION.read_text(encoding="utf-8")
    assert [book["barcode"] for book in qualification["books"]] == sorted(
        book["barcode"] for book in qualification["books"]
    )


def test_artifact_and_audit_hash_contract(qualification, audit):
    assert sha256_file(AUDIT) == EXPECTED_AUDIT_SHA256
    assert qualification["artifacts"]["candidate"]["sha256"] == EXPECTED_CANDIDATE_SHA256
    assert (
        qualification["artifacts"]["candidate"]["file_name"]
        == "principia-34-candidate-20260826-r8.parquet"
    )
    assert qualification["artifacts"]["candidate"]["size_bytes"] == 23_111_880
    assert qualification["artifacts"]["candidate"]["row_count"] == 34
    assert qualification["artifacts"]["quality_audit"]["sha256"] == EXPECTED_AUDIT_SHA256
    assert qualification["artifacts"]["raw_source"] == audit["inputs"]["raw"]
    assert qualification["artifacts"]["baseline_candidate"] == audit["inputs"]["baseline"]
    assert qualification["manual_review_protocol"] == {
        "categories": list(MANUAL_CATEGORIES),
        "classification": "primary_exclusive",
        "sample_seed_sha256": audit["blind_samples"]["sample_seed_sha256"],
        "sample_windows": 64,
    }
    assert qualification["artifacts"]["candidate"] == audit["inputs"]["processed"] | {
        "file_name": "principia-34-candidate-20260826-r8.parquet"
    }
    if CANDIDATE is not None and CANDIDATE.exists():
        assert sha256_file(CANDIDATE) == EXPECTED_CANDIDATE_SHA256


def test_unique_barcodes_and_text_hashes_match_audit(qualification, audit):
    manifest = {book["barcode"]: book for book in qualification["books"]}
    audited = {book["barcode"]: book for book in audit["books"]}

    assert len(manifest) == len(audited) == 34
    assert len({book["text_sha256"] for book in manifest.values()}) == 34
    for barcode, book in audited.items():
        assert manifest[barcode]["text_sha256"] == book["processed"]["text_sha256"]


def test_external_candidate_matches_manifest_when_available(qualification, candidate_records):
    manifest = {book["barcode"]: book for book in qualification["books"]}
    candidate = {record["barcode"]: record for record in candidate_records}

    assert len(candidate) == 34
    for barcode, record in candidate.items():
        assert manifest[barcode]["title"] == record["title"]
        assert (
            manifest[barcode]["text_sha256"]
            == hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
        )


def test_selected_automatic_metrics_match_frozen_audit(qualification, audit):
    manifest = {book["barcode"]: book for book in qualification["books"]}
    audit_books = {book["barcode"]: book for book in audit["books"]}
    for barcode, book in manifest.items():
        source = audit_books[barcode]
        assert book["text_sha256"] == source["processed"]["text_sha256"]
        assert book["raw_text_sha256"] == source["raw"]["text_sha256"]
        assert book["automatic_metrics"]["hard_error_counts"] == {
            name: metric["count"] for name, metric in source["processed"]["hard_errors"].items()
        }
        assert book["automatic_metrics"]["review_heuristic_counts"] == {
            name: metric["count"]
            for name, metric in source["processed"]["review_heuristics"].items()
        }


def test_tier_role_and_token_sums_are_self_consistent(qualification):
    books = qualification["books"]
    summary = qualification["summary"]
    tier_books = Counter(book["manual_qualification"]["tier"] for book in books)
    tier_tokens = Counter()
    role_books = Counter(book["manual_qualification"]["role"] for book in books)
    role_tokens = Counter()
    for book in books:
        tier_tokens[book["manual_qualification"]["tier"]] += book["qwen_token_count"]
        role_tokens[book["manual_qualification"]["role"]] += book["qwen_token_count"]

    assert summary["qwen_token_count"] == 10_075_919
    assert summary["tier_book_counts"] == {"GOLD": 1, "HOLD": 19, "REVIEW": 14}
    assert summary["tier_book_counts"] == dict(sorted(tier_books.items()))
    assert summary["tier_token_counts"] == dict(sorted(tier_tokens.items()))
    assert summary["role_book_counts"] == dict(sorted(role_books.items()))
    assert summary["role_token_counts"] == dict(sorted(role_tokens.items()))
    assert sum(summary["tier_token_counts"].values()) == summary["qwen_token_count"]
    assert sum(summary["role_token_counts"].values()) == summary["qwen_token_count"]


def test_manual_primary_exclusive_ledger_is_complete(qualification):
    category_totals = Counter()
    finding_total = 0
    for book in qualification["books"]:
        manual = book["manual_qualification"]
        assert manual["classification"] == "primary_exclusive"
        assert manual["sample_windows"] == 64
        assert set(manual["finding_counts"]) == set(MANUAL_CATEGORIES)
        assert sum(manual["finding_counts"].values()) == manual["finding_count"]
        assert manual["reason"]
        category_totals.update(manual["finding_counts"])
        finding_total += manual["finding_count"]

    assert qualification["summary"]["manual_category_totals"] == dict(category_totals)
    assert (
        qualification["summary"]["manual_primary_exclusive_finding_count"] == finding_total == 402
    )


def test_gold_gate_is_zero_finding_native_context_anchor(qualification):
    books = {book["barcode"]: book for book in qualification["books"]}
    gold = books["HN6KER"]

    assert gold["manual_qualification"]["tier"] == "GOLD"
    assert gold["manual_qualification"]["role"] == "gold_native_context_anchor"
    assert gold["manual_qualification"]["finding_count"] == 0
    assert sum(gold["automatic_metrics"]["hard_error_counts"].values()) == 0
    assert gold["qwen_token_count"] == qualification["gold_gate"]["qwen_token_count"] == 52_500
    assert gold["qwen_token_count"] < qualification["gold_gate"]["native_context_ceiling_tokens"]
    assert (
        "cannot validate behavior beyond 262,144 tokens" in qualification["gold_gate"]["limitation"]
    )
    assert "1,000,000 tokens" in qualification["gold_gate"]["limitation"]
    assert qualification["gold_gate"]["whole_book_census"] == {
        "source_page_boundaries_reviewed": 194,
        "ordered_numbered_paragraphs": 315,
        "chapters": 15,
        "sections": 31,
        "footnote_blocks": 25,
    }


def test_duplicate_group_excludes_davis_1900(qualification):
    duplicate = qualification["duplicate_group"]
    books = {book["barcode"]: book for book in qualification["books"]}

    assert duplicate["long_line_overlap_percent"] == 92.70
    assert duplicate["word_25_shingle_overlap_percent"] == 88.28
    assert duplicate["shared_25_word_shingle_count"] == 216_089
    assert duplicate["excluded_barcode"] == "32044103157418"
    assert books["32044103157418"]["manual_qualification"]["role"] == "duplicate_excluded"
    assert books["HWQTYU"]["manual_qualification"]["role"] == "hold"


def test_transform_risk_and_history_are_frozen(qualification):
    remove = qualification["shared_transform_risk"]["remove_ocr_artifacts"]
    digit = qualification["shared_transform_risk"]["fix_digit_letter_confusion"]

    assert remove["would_remove_character_count"] == 14_934
    assert (
        remove["punctuation_cluster_character_count"]
        + remove["isolated_special_character_count"]
        + remove["repeated_run_character_count"]
        == remove["would_remove_character_count"]
    )
    assert remove["isolated_special_linefeed_count"] == 1_508
    assert remove["used_by_book_count"] == digit["used_by_book_count"] == 0
    assert digit["raw_candidate_count"] == 6
    assert digit["math_like_candidate_count"] == 4
    history = " ".join(entry["decision"] for entry in qualification["qualification_history"])
    assert "intentional high-recall Phase-0 triage" in history
    assert "preservation and evidence" in history


def test_manifest_contains_no_book_text_or_excerpts(qualification):
    forbidden_keys = {"text", "excerpt", "window_text", "first_500", "last_500"}

    def visit(value):
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(qualification)
    assert qualification["content_policy"] == {
        "contains_source_text": False,
        "contains_excerpts": False,
        "data_artifacts_committed": False,
    }
    assert "/mnt/" not in QUALIFICATION.read_text(encoding="utf-8")


def test_builder_reconstructs_committed_manifest(qualification, audit, candidate_records):
    token_counts = {book["barcode"]: book["qwen_token_count"] for book in qualification["books"]}
    rebuilt = build_qualification(
        candidate_records,
        audit,
        candidate_artifact=qualification["artifacts"]["candidate"],
        audit_artifact=qualification["artifacts"]["quality_audit"],
        tokenizer=qualification["tokenizer"],
        model_configs=qualification["model_configs"],
        token_counts=token_counts,
    )

    assert rebuilt == qualification


def test_compute_token_counts_disables_special_tokens():
    class FakeTokenizer:
        def __init__(self):
            self.calls = []

        def encode(self, text, *, add_special_tokens):
            self.calls.append((text, add_special_tokens))
            return text.split()

    tokenizer = FakeTokenizer()
    counts = compute_token_counts(
        [
            {"barcode": "one", "text": "alpha beta"},
            {"barcode": "two", "text": "gamma"},
        ],
        tokenizer,
    )

    assert counts == {"one": 2, "two": 1}
    assert tokenizer.calls == [("alpha beta", False), ("gamma", False)]
