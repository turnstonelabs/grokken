#!/usr/bin/env python3
"""Build the deterministic final Principia-34 qualification manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

SCHEMA_VERSION = "principia-34-qualification-v1"
QUALIFICATION_ID = "principia-34-r8-20260826"
EXPECTED_CANDIDATE_SHA256 = "07f9c9a2b29b155077bc8e294fc9ed558c2a3457ce0c08f915174150928e3a87"
EXPECTED_CANDIDATE_SIZE = 23_111_880
EXPECTED_AUDIT_SHA256 = "4343034d4c2f20b616ab5d3148d4a338a2c0318f55fb00802b1418431c4bd928"
EXPECTED_SOURCE_CONFIG_SHA256 = "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab"
EXPECTED_STATIC_CONFIG_SHA256 = "1473020b606e0a85a13e6c1fdc72427c0e718c71a92ab27d43cf9b1560f9a329"
EXPECTED_STATIC_PROFILE_SHA256 = "61c58513aba12ddfb439736c4a85b2aba387776afffd7f742a247d48938aaa2a"
EXPECTED_SAMPLE_SEED_SHA256 = "08d097cd91f23d901097ffb82f8267797d90463c2ca70329ecce4642cbb22ba7"
EXPECTED_SAMPLE_WINDOWS = 64
EXPECTED_BOOK_COUNT = 34

TOKENIZER_FILE_HASHES = {
    "chat_template.jinja": "c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041",
    "merges.txt": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d",
    "tokenizer.json": "0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3",
    "tokenizer_config.json": "b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27",
    "vocab.json": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003",
}

MANUAL_CATEGORIES = (
    "header_or_folio",
    "split_word",
    "ocr_glyph_or_punctuation",
    "layout_or_other",
)

# barcode: (batch, tier, total, H, S, O, L)
_MANUAL_ROWS = {
    "32044097009690": ("A", "REVIEW", 6, 0, 6, 0, 0),
    "HN2WWN": ("A", "REVIEW", 9, 0, 5, 3, 1),
    "HWT5II": ("A", "REVIEW", 6, 1, 4, 1, 0),
    "HNU1G9": ("A", "REVIEW", 10, 1, 4, 5, 0),
    "AH3KTH": ("A", "REVIEW", 3, 0, 2, 1, 0),
    "HWKBVP": ("A", "REVIEW", 11, 0, 7, 3, 1),
    "32044038386975": ("A", "HOLD", 15, 6, 5, 3, 1),
    "AH45Q4": ("A", "HOLD", 8, 2, 2, 2, 2),
    "HWABNK": ("B", "REVIEW", 13, 0, 6, 5, 2),
    "HWJN82": ("B", "REVIEW", 15, 2, 7, 4, 2),
    "HWPLDT": ("B", "HOLD", 13, 4, 2, 2, 5),
    "AH3HJZ": ("B", "HOLD", 15, 1, 5, 6, 3),
    "HN28C4": ("B", "REVIEW", 15, 2, 7, 3, 3),
    "HNVJ7R": ("B", "HOLD", 19, 3, 4, 7, 5),
    "TZ1WHG": ("B", "HOLD", 15, 1, 4, 4, 6),
    "32044103157418": ("B", "HOLD", 14, 1, 5, 2, 6),
    "HWQTYU": ("C", "HOLD", 10, 1, 4, 2, 3),
    "32044103157517": ("C", "HOLD", 16, 4, 2, 0, 10),
    "32044069804946": ("C", "HOLD", 8, 0, 2, 2, 4),
    "HWQXIB": ("C", "HOLD", 14, 1, 1, 2, 10),
    "32044097047575": ("C", "HOLD", 14, 2, 1, 5, 6),
    "HN6KER": ("C", "GOLD", 0, 0, 0, 0, 0),
    "HC1BZF": ("C", "REVIEW", 3, 0, 2, 1, 0),
    "HWK6N4": ("C", "HOLD", 16, 2, 7, 2, 5),
    "32044018740308": ("D", "REVIEW", 1, 0, 1, 0, 0),
    "HXQ9SJ": ("D", "REVIEW", 4, 1, 2, 1, 0),
    "LI3QQB": ("D", "HOLD", 8, 0, 2, 5, 1),
    "32044097049340": ("D", "HOLD", 9, 0, 5, 0, 4),
    "TZ1HCP": ("D", "HOLD", 13, 0, 3, 8, 2),
    "32044020258091": ("D", "HOLD", 9, 1, 3, 5, 0),
    "32044094451689": ("D", "HOLD", 10, 0, 3, 6, 1),
    "32044018647321": ("D", "HOLD", 16, 1, 5, 1, 9),
    "32044010149714": ("validation", "REVIEW", 37, 1, 14, 9, 13),
    "32044072043805": ("validation", "REVIEW", 27, 0, 5, 4, 18),
}

_MANUAL_REASONS = {
    "32044010149714": (
        "Correct bounded repairs, with dense residual split, OCR, and layout findings."
    ),
    "32044018647321": "Pervasive marginal and column interleaving.",
    "32044018740308": "One residual word continuation.",
    "32044020258091": "Residual folio, word continuations, and OCR artifacts.",
    "32044038386975": "Recurrent page furniture plus cropped and figure OCR.",
    "32044069804946": "Footnote and reading-order interruptions, word wraps, and OCR artifacts.",
    "32044072043805": "Verified r8 joins are safe; legacy layout, OCR, and word wraps remain.",
    "32044094451689": "Quote and punctuation OCR, missing-text OCR, and word continuations.",
    "32044097009690": "Residual word continuations; mathematical formulas were preserved.",
    "32044097047575": "Figures and questions displace prose, with residual OCR and page heads.",
    "32044097049340": "Malformed tables and contents plus reordered body text.",
    "32044103157418": (
        "Misordered contents, columns, and footnotes; also excluded as a near duplicate."
    ),
    "32044103157517": "Systematic marginal-heading and two-column interleaving.",
    "AH3HJZ": "OCR debris and truncated fragments indicate unstable text.",
    "AH3KTH": "Two word continuations and one isolated prose OCR bar.",
    "AH45Q4": "Residual page furniture and interleaved prose.",
    "HC1BZF": "Two caption-to-prose ordering seams and one punctuation OCR error.",
    "HN28C4": "Recurring word continuations and two running heads without broad column damage.",
    "HN2WWN": "Word continuations, localized prose OCR, and figure-layout debris.",
    "HN6KER": (
        "Whole-book census found no known material content, OCR, furniture, or order blocker."
    ),
    "HNU1G9": "Inline running head and folio, word continuations, and numeric-reference OCR.",
    "HNVJ7R": "Corrupted Greek plus index and page-number reordering.",
    "HWABNK": "Word continuations and punctuation OCR with little structural damage.",
    "HWJN82": "Mostly mechanical word splits and residual head or signature furniture.",
    "HWK6N4": "Two-column verse is interleaved with word wraps and page artifacts.",
    "HWKBVP": "Verse and glossary wraps, numeral OCR, and one ordering defect.",
    "HWPLDT": "Severe two-column interleaving and retained page furniture.",
    "HWQTYU": "Corrupt contents layout, orphan furniture, word wraps, and OCR or column seams.",
    "HWQXIB": "Marginal headings repeatedly interrupt prose, with page junk and OCR.",
    "HWT5II": "Signature or page split, ordinary word wraps, and omitted-word OCR.",
    "HXQ9SJ": "Residual folio, word continuations, and isolated OCR.",
    "LI3QQB": "OCR-glyph density, word continuations, and one layout defect.",
    "TZ1HCP": "Displaced fragments and extraneous-script OCR.",
    "TZ1WHG": "Footnotes and page rules intrude into body flow.",
}

SPECIAL_ROLES = {
    "HN6KER": "gold_native_context_anchor",
    "HC1BZF": "provisional_over_262k_candidate",
    "AH3KTH": "near_1m_repair_candidate",
    "HWKBVP": "factor_4_repair_candidate",
    "32044103157418": "duplicate_excluded",
    "32044010149714": "holdout_repair",
    "32044072043805": "holdout_repair",
}

TIER_DEFINITIONS = {
    "GOLD": (
        "Zero hard errors; exhaustive residual disposition; no known material layout or "
        "source-order blocker; zero actionable fixed-seed windows; deterministic handler "
        "parity; and no duplicate leakage."
    ),
    "REVIEW": (
        "Preservation-safe enough for bounded manual repair, but known cleanup remains; "
        "not automatic permission to train."
    ),
    "HOLD": ("A material OCR, layout, ordering, or duplication blocker remains."),
}

ROLE_DEFINITIONS = {
    "gold_native_context_anchor": (
        "Gold preservation anchor inside its observed native-length context; "
        "not an extension proof."
    ),
    "provisional_over_262k_candidate": (
        "Provisional source long enough to probe beyond 262,144 tokens after targeted repair."
    ),
    "near_1m_repair_candidate": (
        "Near-million-token source reserved for repair and requalification."
    ),
    "factor_4_repair_candidate": (
        "Source long enough for factor-4 geometry work, reserved for repair and requalification."
    ),
    "duplicate_excluded": "Excluded member of the declared cross-edition duplicate group.",
    "holdout_repair": "Reserved validation source requiring repair; excluded from training.",
    "review_candidate": "Non-special review-tier candidate requiring targeted review or repair.",
    "hold": "Non-special hold-tier source pending repair or explicit exception.",
}

HARD_ERROR_METRICS = (
    "private_use_character",
    "replacement_character",
    "soft_hyphen",
    "unassigned_or_surrogate_character",
    "unexpected_control_character",
)

REVIEW_METRICS = (
    "consecutive_duplicate_line",
    "global_recurrent_line",
    "isolated_page_number",
    "line_end_hyphenation",
    "line_over_1000_characters",
    "line_over_300_characters",
    "pathological_punctuation",
    "pathological_whitespace",
    "repeated_header_footer",
    "suspicious_ocr_glyph",
    "very_short_line",
)


def sha256_file(path: Path) -> str:
    """Hash a file without loading it all into memory."""

    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _artifact(path: Path) -> dict[str, object]:
    return {
        "file_name": path.name,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def _verify_artifact(
    metadata: Mapping[str, object], *, expected_sha256: str, expected_size: int | None = None
) -> None:
    if metadata["sha256"] != expected_sha256:
        raise ValueError(
            f"artifact SHA256 mismatch: expected {expected_sha256}, got {metadata['sha256']}"
        )
    if expected_size is not None and metadata["size_bytes"] != expected_size:
        raise ValueError(
            f"artifact size mismatch: expected {expected_size}, got {metadata['size_bytes']}"
        )


def _index_records(records: Iterable[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    required = {
        "barcode",
        "title",
        "text",
        "raw_chars",
        "processed_chars",
        "reduction_pct",
        "transforms_applied",
    }
    for row_number, record in enumerate(records):
        missing = required - set(record)
        if missing:
            raise ValueError(f"candidate row {row_number} missing fields {sorted(missing)}")
        barcode = record["barcode"]
        title = record["title"]
        text = record["text"]
        if not isinstance(barcode, str) or not barcode:
            raise ValueError(f"candidate row {row_number} has invalid barcode")
        if not isinstance(title, str) or not title:
            raise ValueError(f"candidate row {row_number} has invalid title")
        if not isinstance(text, str):
            raise ValueError(f"candidate row {row_number} has non-string text")
        if barcode in indexed:
            raise ValueError(f"candidate contains duplicate barcode {barcode!r}")
        indexed[barcode] = record
    if len(indexed) != EXPECTED_BOOK_COUNT:
        raise ValueError(f"candidate must contain exactly {EXPECTED_BOOK_COUNT} books")
    return indexed


def _index_audit_books(audit: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    books = audit.get("books")
    if not isinstance(books, list):
        raise ValueError("audit books must be a list")
    indexed: dict[str, Mapping[str, object]] = {}
    for book in books:
        if not isinstance(book, Mapping) or not isinstance(book.get("barcode"), str):
            raise ValueError("audit contains an invalid book record")
        barcode = str(book["barcode"])
        if barcode in indexed:
            raise ValueError(f"audit contains duplicate barcode {barcode!r}")
        indexed[barcode] = book
    return indexed


def _index_baseline_books(audit: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    baseline_diff = audit.get("baseline_diff")
    if not isinstance(baseline_diff, Mapping) or not isinstance(baseline_diff.get("books"), list):
        raise ValueError("audit baseline_diff books are missing")
    return {str(book["barcode"]): book for book in baseline_diff["books"]}


def _verify_audit_contract(
    audit: Mapping[str, object],
    *,
    candidate_artifact: Mapping[str, object],
    candidate_barcodes: set[str],
) -> None:
    if audit.get("schema_version") != "principia-quality-audit-v2":
        raise ValueError("unexpected audit schema version")
    if audit.get("book_count") != EXPECTED_BOOK_COUNT:
        raise ValueError("audit must cover exactly 34 books")

    inputs = audit.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ValueError("audit inputs are missing")
    processed = inputs.get("processed")
    baseline = inputs.get("baseline")
    raw = inputs.get("raw")
    if not all(isinstance(item, Mapping) for item in (processed, baseline, raw)):
        raise ValueError("audit raw/baseline/processed input metadata are missing")
    if processed["sha256"] != candidate_artifact["sha256"]:
        raise ValueError("audit processed SHA256 differs from candidate artifact")
    if processed["size_bytes"] != candidate_artifact["size_bytes"]:
        raise ValueError("audit processed size differs from candidate artifact")
    if processed["row_count"] != EXPECTED_BOOK_COUNT:
        raise ValueError("audit processed row count must be 34")

    blind = audit.get("blind_samples")
    if not isinstance(blind, Mapping):
        raise ValueError("audit blind sample manifest is missing")
    if blind.get("processed_artifact_sha256") != candidate_artifact["sha256"]:
        raise ValueError("blind sample artifact SHA256 differs from candidate")
    if blind.get("sample_seed_sha256") != EXPECTED_SAMPLE_SEED_SHA256:
        raise ValueError("unexpected blind sample seed")
    if blind.get("sample_seed_sha256") != baseline["sha256"]:
        raise ValueError("blind sample seed must equal the baseline artifact SHA256")
    if blind.get("sample_windows_per_book") != EXPECTED_SAMPLE_WINDOWS:
        raise ValueError("blind sample manifest must use 64 windows per book")
    blind_books = blind.get("books")
    if not isinstance(blind_books, list):
        raise ValueError("blind sample books are missing")
    blind_index = {str(book["barcode"]): book for book in blind_books}
    if set(blind_index) != candidate_barcodes or len(blind_index) != EXPECTED_BOOK_COUNT:
        raise ValueError("blind sample barcode coverage differs from candidate")
    if any(
        len(book.get("samples", [])) != EXPECTED_SAMPLE_WINDOWS for book in blind_index.values()
    ):
        raise ValueError("every blind sample book must contain 64 windows")


def compute_token_counts(
    records: Iterable[Mapping[str, object]], tokenizer: object
) -> dict[str, int]:
    """Count Qwen tokens with the supplied tokenizer and no special tokens."""

    counts: dict[str, int] = {}
    encode = getattr(tokenizer, "encode", None)
    if not callable(encode):
        raise TypeError("tokenizer must expose encode(text, add_special_tokens=False)")
    for record in records:
        barcode = record.get("barcode")
        text = record.get("text")
        if not isinstance(barcode, str) or not isinstance(text, str):
            raise ValueError("token-count records require string barcode and text")
        if barcode in counts:
            raise ValueError(f"token-count records contain duplicate barcode {barcode!r}")
        counts[barcode] = len(encode(text, add_special_tokens=False))
    return counts


def tokenizer_metadata(
    tokenizer_path: Path, tokenizer: object, transformers_version: str
) -> dict[str, object]:
    """Hash the exact local tokenizer inputs and describe the count method."""

    files: dict[str, object] = {}
    aggregate = hashlib.sha256()
    for name, expected_sha256 in sorted(TOKENIZER_FILE_HASHES.items()):
        path = tokenizer_path / name
        metadata = _artifact(path)
        if metadata["sha256"] != expected_sha256:
            raise ValueError(f"tokenizer file {name} has unexpected SHA256")
        files[name] = {
            "sha256": metadata["sha256"],
            "size_bytes": metadata["size_bytes"],
        }
        aggregate.update(name.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(expected_sha256.encode("ascii"))
        aggregate.update(b"\0")
    return {
        "snapshot_name": tokenizer_path.name,
        "loader": (
            "transformers.AutoTokenizer.from_pretrained("
            "local_files_only=True, trust_remote_code=False)"
        ),
        "token_count_method": "len(tokenizer.encode(text, add_special_tokens=False))",
        "add_special_tokens": False,
        "transformers_version": transformers_version,
        "tokenizer_class": type(tokenizer).__name__,
        "vocab_size": int(getattr(tokenizer, "vocab_size")),
        "files": files,
        "files_aggregate_sha256": aggregate.hexdigest(),
        "files_aggregate_method": "SHA256(relative_name_utf8 + NUL + file_sha256_ascii + NUL)",
    }


def _manual_record(barcode: str) -> dict[str, object]:
    batch, tier, expected_total, *category_values = _MANUAL_ROWS[barcode]
    counts = dict(zip(MANUAL_CATEGORIES, category_values, strict=True))
    if sum(counts.values()) != expected_total:
        raise ValueError(f"manual ledger total mismatch for {barcode}")
    role = SPECIAL_ROLES.get(barcode)
    if role is None:
        role = "review_candidate" if tier == "REVIEW" else "hold"
    return {
        "batch": batch,
        "tier": tier,
        "role": role,
        "classification": "primary_exclusive",
        "sample_windows": EXPECTED_SAMPLE_WINDOWS,
        "finding_count": expected_total,
        "finding_counts": counts,
        "reason": _MANUAL_REASONS[barcode],
    }


def _automatic_metrics(audit_book: Mapping[str, object]) -> dict[str, object]:
    processed = audit_book["processed"]
    hard_errors = processed["hard_errors"]
    review = processed["review_heuristics"]
    comparison = audit_book["raw_to_processed"]
    return {
        "hard_error_counts": {name: int(hard_errors[name]["count"]) for name in HARD_ERROR_METRICS},
        "review_heuristic_counts": {name: int(review[name]["count"]) for name in REVIEW_METRICS},
        "retention_ratios": {
            name: comparison["retention"][name]["ratio"]
            for name in (
                "characters",
                "non_whitespace_characters",
                "alphanumeric_characters",
                "physical_lines",
                "nonempty_lines",
            )
        },
    }


def _aggregate_counts(books: Sequence[Mapping[str, object]]) -> dict[str, object]:
    tier_book_counts = Counter(str(book["manual_qualification"]["tier"]) for book in books)
    tier_token_counts: Counter[str] = Counter()
    role_book_counts = Counter(str(book["manual_qualification"]["role"]) for book in books)
    role_token_counts: Counter[str] = Counter()
    manual_category_totals: Counter[str] = Counter()
    for book in books:
        tokens = int(book["qwen_token_count"])
        manual = book["manual_qualification"]
        tier_token_counts[str(manual["tier"])] += tokens
        role_token_counts[str(manual["role"])] += tokens
        manual_category_totals.update(manual["finding_counts"])
    return {
        "book_count": len(books),
        "qwen_token_count": sum(int(book["qwen_token_count"]) for book in books),
        "tier_book_counts": dict(sorted(tier_book_counts.items())),
        "tier_token_counts": dict(sorted(tier_token_counts.items())),
        "role_book_counts": dict(sorted(role_book_counts.items())),
        "role_token_counts": dict(sorted(role_token_counts.items())),
        "manual_primary_exclusive_finding_count": sum(manual_category_totals.values()),
        "manual_category_totals": {
            name: manual_category_totals[name] for name in MANUAL_CATEGORIES
        },
    }


def build_qualification(
    records: Iterable[Mapping[str, object]],
    audit: Mapping[str, object],
    *,
    candidate_artifact: Mapping[str, object],
    audit_artifact: Mapping[str, object],
    tokenizer: Mapping[str, object],
    model_configs: Mapping[str, object],
    token_counts: Mapping[str, int],
) -> dict[str, object]:
    """Join the frozen automatic audit and curated manual qualification ledger."""

    _verify_artifact(
        candidate_artifact,
        expected_sha256=EXPECTED_CANDIDATE_SHA256,
        expected_size=EXPECTED_CANDIDATE_SIZE,
    )
    _verify_artifact(audit_artifact, expected_sha256=EXPECTED_AUDIT_SHA256)
    candidate = _index_records(records)
    if set(candidate) != set(_MANUAL_ROWS):
        raise ValueError("manual ledger barcode coverage differs from candidate")
    if set(token_counts) != set(candidate):
        raise ValueError("token-count barcode coverage differs from candidate")

    audit_books = _index_audit_books(audit)
    baseline_books = _index_baseline_books(audit)
    if set(audit_books) != set(candidate) or set(baseline_books) != set(candidate):
        raise ValueError("audit book coverage differs from candidate")
    _verify_audit_contract(
        audit,
        candidate_artifact=candidate_artifact,
        candidate_barcodes=set(candidate),
    )

    books: list[dict[str, object]] = []
    text_set_hasher = hashlib.sha256()
    for barcode in sorted(candidate):
        record = candidate[barcode]
        text = str(record["text"])
        text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        audit_book = audit_books[barcode]
        audit_processed = audit_book["processed"]
        if audit_processed["text_sha256"] != text_sha256:
            raise ValueError(f"candidate text SHA256 differs from audit for {barcode}")
        if int(record["processed_chars"]) != len(text):
            raise ValueError(f"candidate processed_chars differs from text length for {barcode}")
        if int(audit_processed["counts"]["characters"]) != len(text):
            raise ValueError(f"audit processed character count differs for {barcode}")
        if int(audit_book["raw"]["counts"]["characters"]) != int(record["raw_chars"]):
            raise ValueError(f"audit raw character count differs for {barcode}")
        if baseline_books[barcode]["candidate_text_sha256"] != text_sha256:
            raise ValueError(f"baseline diff candidate SHA256 differs for {barcode}")
        if int(token_counts[barcode]) <= 0:
            raise ValueError(f"token count must be positive for {barcode}")

        text_set_hasher.update(barcode.encode("utf-8"))
        text_set_hasher.update(b"\0")
        text_set_hasher.update(text_sha256.encode("ascii"))
        text_set_hasher.update(b"\0")
        books.append(
            {
                "barcode": barcode,
                "title": str(record["title"]),
                "text_sha256": text_sha256,
                "raw_text_sha256": str(audit_book["raw"]["text_sha256"]),
                "baseline_text_sha256": str(baseline_books[barcode]["baseline_text_sha256"]),
                "qwen_token_count": int(token_counts[barcode]),
                "source_counts": {
                    "raw_characters": int(record["raw_chars"]),
                    "processed_characters": int(record["processed_chars"]),
                    "processed_nonempty_lines": int(audit_processed["counts"]["nonempty_lines"]),
                    "processed_physical_lines": int(audit_processed["counts"]["physical_lines"]),
                    "reduction_percent": float(record["reduction_pct"]),
                    "transforms_applied": int(record["transforms_applied"]),
                },
                "automatic_metrics": _automatic_metrics(audit_book),
                "manual_qualification": _manual_record(barcode),
            }
        )

    expected_text_set = audit["aggregate"]["processed"]["text_set_sha256"]
    if text_set_hasher.hexdigest() != expected_text_set:
        raise ValueError("candidate text-set SHA256 differs from audit aggregate")

    summary = _aggregate_counts(books)
    if summary["tier_book_counts"] != {"GOLD": 1, "HOLD": 19, "REVIEW": 14}:
        raise ValueError("manual tier totals differ from the frozen qualification")
    gold = next(book for book in books if book["manual_qualification"]["tier"] == "GOLD")
    if gold["barcode"] != "HN6KER" or gold["manual_qualification"]["finding_count"] != 0:
        raise ValueError("gold gate requires zero findings for HN6KER")

    audit_inputs = audit["inputs"]
    return {
        "schema_version": SCHEMA_VERSION,
        "qualification_id": QUALIFICATION_ID,
        "status": "qualified_with_tiered_repair_gates",
        "content_policy": {
            "contains_source_text": False,
            "contains_excerpts": False,
            "data_artifacts_committed": False,
        },
        "artifacts": {
            "candidate": {**candidate_artifact, "row_count": EXPECTED_BOOK_COUNT},
            "quality_audit": {**audit_artifact, "schema_version": audit["schema_version"]},
            "raw_source": dict(audit_inputs["raw"]),
            "baseline_candidate": dict(audit_inputs["baseline"]),
        },
        "model_configs": dict(model_configs),
        "tokenizer": dict(tokenizer),
        "automatic_metric_source": {
            "audit_sha256": audit_artifact["sha256"],
            "audit_schema_version": audit["schema_version"],
            "hard_error_metrics": list(HARD_ERROR_METRICS),
            "review_heuristic_metrics": list(REVIEW_METRICS),
        },
        "manual_review_protocol": {
            "classification": "primary_exclusive",
            "sample_seed_sha256": EXPECTED_SAMPLE_SEED_SHA256,
            "sample_windows": EXPECTED_SAMPLE_WINDOWS,
            "categories": list(MANUAL_CATEGORIES),
        },
        "tier_definitions": TIER_DEFINITIONS,
        "role_definitions": ROLE_DEFINITIONS,
        "summary": summary,
        "gold_gate": {
            "barcode": gold["barcode"],
            "qwen_token_count": gold["qwen_token_count"],
            "manual_primary_exclusive_finding_count": 0,
            "scope": "native_context_preservation_anchor_only",
            "native_context_ceiling_tokens": 262_144,
            "target_context_tokens": 1_000_000,
            "limitation": (
                "This approximately 52.5k-token gold seed cannot validate behavior beyond "
                "262,144 tokens or at 1,000,000 tokens."
            ),
            "whole_book_census": {
                "source_page_boundaries_reviewed": 194,
                "ordered_numbered_paragraphs": 315,
                "chapters": 15,
                "sections": 31,
                "footnote_blocks": 25,
            },
        },
        "training_scope": {
            "currently_gold_token_count": 52_500,
            "validation_holdout_token_count": 644_361,
            "duplicate_excluded_token_count": 395_269,
            "non_holdout_nonduplicate_token_count": 9_036_289,
            "non_holdout_nonduplicate_requires_tier_specific_repair": True,
        },
        "duplicate_group": {
            "group": "davis_elements_of_international_law_1900_1903",
            "barcodes": ["32044103157418", "HWQTYU"],
            "long_line_overlap_percent": 92.70,
            "word_25_shingle_overlap_percent": 88.28,
            "shared_25_word_shingle_count": 216_089,
            "excluded_barcode": "32044103157418",
            "excluded_role": "duplicate_excluded",
        },
        "shared_transform_risk": {
            "remove_ocr_artifacts": {
                "would_remove_character_count": 14_934,
                "punctuation_cluster_character_count": 7_145,
                "isolated_special_character_count": 7_679,
                "isolated_special_linefeed_count": 1_508,
                "repeated_run_character_count": 110,
                "used_by_book_count": 0,
                "book_count": EXPECTED_BOOK_COUNT,
            },
            "fix_digit_letter_confusion": {
                "used_by_book_count": 0,
                "book_count": EXPECTED_BOOK_COUNT,
                "raw_candidate_count": 6,
                "math_like_candidate_count": 4,
            },
        },
        "qualification_history": [
            {
                "stage": "phase_0",
                "decision": (
                    "Broad dehyphenation was intentional high-recall Phase-0 triage, "
                    "not final gold evidence."
                ),
            },
            {
                "stage": "r8_final_qualification",
                "decision": (
                    "Gold status uses preservation and evidence from the fixed-seed blind review."
                ),
            },
        ],
        "books": books,
    }


def render_json(qualification: Mapping[str, object]) -> str:
    """Serialize qualification deterministically."""

    return json.dumps(qualification, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _model_configs(
    native_config: Path, static_config: Path, static_profile: Path
) -> dict[str, object]:
    files = {
        "native_qwen_config": (
            native_config,
            EXPECTED_SOURCE_CONFIG_SHA256,
        ),
        "static_yarn4_config": (
            static_config,
            EXPECTED_STATIC_CONFIG_SHA256,
        ),
        "static_yarn4_profile": (
            static_profile,
            EXPECTED_STATIC_PROFILE_SHA256,
        ),
    }
    result: dict[str, object] = {}
    for name, (path, expected_sha256) in files.items():
        metadata = _artifact(path)
        if metadata["sha256"] != expected_sha256:
            raise ValueError(f"{name} has unexpected SHA256")
        result[name] = metadata
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Build or verify the frozen qualification JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--tokenizer", required=True, type=Path)
    parser.add_argument("--native-config", required=True, type=Path)
    parser.add_argument("--static-config", required=True, type=Path)
    parser.add_argument("--static-profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    candidate_artifact = _artifact(args.candidate)
    audit_artifact = _artifact(args.audit)
    _verify_artifact(
        candidate_artifact,
        expected_sha256=EXPECTED_CANDIDATE_SHA256,
        expected_size=EXPECTED_CANDIDATE_SIZE,
    )
    _verify_artifact(audit_artifact, expected_sha256=EXPECTED_AUDIT_SHA256)

    import pandas as pd
    import transformers
    from transformers import AutoTokenizer

    records = pd.read_parquet(args.candidate).to_dict(orient="records")
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer,
        local_files_only=True,
        trust_remote_code=False,
    )
    token_counts = compute_token_counts(records, tokenizer)
    qualification = build_qualification(
        records,
        audit,
        candidate_artifact=candidate_artifact,
        audit_artifact=audit_artifact,
        tokenizer=tokenizer_metadata(args.tokenizer, tokenizer, transformers.__version__),
        model_configs=_model_configs(
            args.native_config,
            args.static_config,
            args.static_profile,
        ),
        token_counts=token_counts,
    )
    encoded = render_json(qualification)
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != encoded:
            raise ValueError("qualification output differs from deterministic rebuild")
    else:
        with args.output.open("x", encoding="utf-8") as destination:
            destination.write(encoded)
    sys.stdout.write(hashlib.sha256(encoded.encode("utf-8")).hexdigest() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
