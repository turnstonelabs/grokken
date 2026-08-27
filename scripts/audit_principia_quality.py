#!/usr/bin/env python3
"""Audit Principia OCR/layout quality without emitting source text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

SCHEMA_VERSION = "principia-quality-audit-v2"
SAMPLE_SCHEMA_VERSION = "principia-blind-samples-v1"
LINE_NORMALIZATION = "NFKC-whitespace-collapse-casefold-v1"
THRESHOLDS = {
    "duplicate_line_min_run": 2,
    "global_recurrent_line_max_characters": 200,
    "global_recurrent_line_min_characters": 8,
    "global_recurrent_line_min_occurrences": 3,
    "header_footer_max_characters": 100,
    "header_footer_max_words": 14,
    "header_footer_min_occurrences": 3,
    "line_over_1000_characters": 1000,
    "line_over_300_characters": 300,
    "pathological_punctuation_or_symbol_min_run": 6,
    "pathological_space_min_run": 3,
    "very_short_line_max_characters": 3,
}

_PAGE_NUMBER_RE = re.compile(
    r"^(?:(?:\d{1,4}|[ivxlcdm]{1,12})|[\[(]\s*(?:\d{1,4}|[ivxlcdm]{1,12})\s*[\])])$",
    re.IGNORECASE,
)
_TRAILING_WHITESPACE_RE = re.compile(r"[ \t]+(?=\r?$)", re.MULTILINE)
_MULTISPACE_RE = re.compile(rf" {{{THRESHOLDS['pathological_space_min_run']},}}")
_LEGACY_OCR_GLYPHS = frozenset("ſﬀﬁﬂﬃﬄﬅﬆ")
_OCR_ALPHA_CONFUSABLES = frozenset("01|")
_OCR_ADDITIONAL_DIGIT_CONFUSABLES = frozenset("5")
_SCRIPT_CONFUSABLES = frozenset("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧϹαβγεζηικνορτυχϲАВСЕНІЈКМОРЅТХУавсенікморстхујѕ")
_MOJIBAKE_PREFIXES = ("Ã", "Â", "â€", "â€™", "â€œ", "â€\u009d", "ï»¿")
_RETENTION_FIELDS = (
    "characters",
    "non_whitespace_characters",
    "alphanumeric_characters",
    "physical_lines",
    "nonempty_lines",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()


def _measurement(count: int, denominator: int, denominator_unit: str) -> dict[str, object]:
    return {
        "count": count,
        "denominator": denominator,
        "denominator_unit": denominator_unit,
        "rate": count / denominator if denominator else 0.0,
    }


def _is_page_number_candidate(line: str) -> bool:
    stripped = line.strip()
    stripped = re.sub(r"^[—–-]+\s*", "", stripped)
    stripped = re.sub(r"\s*[—–-]+$", "", stripped)
    return bool(stripped and _PAGE_NUMBER_RE.fullmatch(stripped))


def _normalized_line(line: str) -> str:
    normalized = unicodedata.normalize("NFKC", line)
    return " ".join(normalized.split()).casefold()


def _consecutive_duplicate_line_metrics(
    normalized_lines: Sequence[str],
) -> tuple[int, int, int]:
    duplicate_count = 0
    run_count = 0
    max_run_length = 0
    previous = ""
    run_length = 0

    for line in normalized_lines:
        if line and line == previous:
            run_length += 1
        else:
            if run_length >= THRESHOLDS["duplicate_line_min_run"]:
                run_count += 1
                duplicate_count += run_length - 1
                max_run_length = max(max_run_length, run_length)
            run_length = 1 if line else 0
        previous = line

    if run_length >= THRESHOLDS["duplicate_line_min_run"]:
        run_count += 1
        duplicate_count += run_length - 1
        max_run_length = max(max_run_length, run_length)

    return duplicate_count, run_count, max_run_length


def _global_recurrent_line_metrics(normalized_lines: Sequence[str]) -> tuple[int, int, int]:
    counts = Counter(
        line
        for line in normalized_lines
        if THRESHOLDS["global_recurrent_line_min_characters"]
        <= len(line)
        <= THRESHOLDS["global_recurrent_line_max_characters"]
    )
    recurrent_counts = [
        count
        for count in counts.values()
        if count >= THRESHOLDS["global_recurrent_line_min_occurrences"]
    ]
    total_occurrences = sum(recurrent_counts)
    unique_pattern_count = len(recurrent_counts)
    excess_count = total_occurrences - unique_pattern_count
    return total_occurrences, excess_count, unique_pattern_count


def _header_footer_metrics(lines: Sequence[str]) -> tuple[int, int]:
    normalized = [_normalized_line(line) for line in lines]
    counts = Counter(line for line in normalized if line)
    candidates = {
        line
        for line, count in counts.items()
        if count >= THRESHOLDS["header_footer_min_occurrences"]
        and len(line) <= THRESHOLDS["header_footer_max_characters"]
        and len(line.split()) <= THRESHOLDS["header_footer_max_words"]
        and any(character.isalpha() for character in line)
        and not _is_page_number_candidate(line)
    }
    return sum(counts[line] for line in candidates), len(candidates)


def _pathological_whitespace_positions(text: str) -> set[int]:
    positions = {
        index
        for index, character in enumerate(text)
        if character in "\t\r" or (unicodedata.category(character) == "Zs" and character != " ")
    }
    for pattern in (_MULTISPACE_RE, _TRAILING_WHITESPACE_RE):
        for match in pattern.finditer(text):
            positions.update(range(match.start(), match.end()))
    return positions


def _excess_blank_line_count(lines: Sequence[str]) -> int:
    excess = 0
    blank_run = 0
    for line in lines:
        if line.strip():
            excess += max(0, blank_run - 2)
            blank_run = 0
        else:
            blank_run += 1
    return excess + max(0, blank_run - 2)


def _pathological_punctuation_positions(text: str) -> tuple[set[int], int]:
    positions: set[int] = set()
    run_count = 0
    run_start: int | None = None

    for index, character in enumerate(text):
        if unicodedata.category(character)[0] in "PS":
            if run_start is None:
                run_start = index
        elif run_start is not None:
            if index - run_start >= THRESHOLDS["pathological_punctuation_or_symbol_min_run"]:
                positions.update(range(run_start, index))
                run_count += 1
            run_start = None

    if (
        run_start is not None
        and len(text) - run_start >= THRESHOLDS["pathological_punctuation_or_symbol_min_run"]
    ):
        positions.update(range(run_start, len(text)))
        run_count += 1
    return positions, run_count


def _suspicious_ocr_positions(text: str) -> tuple[set[int], dict[str, int]]:
    legacy = {index for index, character in enumerate(text) if character in _LEGACY_OCR_GLYPHS}
    alpha_confusable = {
        index
        for index in range(1, len(text) - 1)
        if text[index] in _OCR_ALPHA_CONFUSABLES
        and text[index - 1].isalpha()
        and text[index + 1].isalpha()
    }
    additional_digit_confusable = {
        index
        for index in range(1, len(text) - 1)
        if text[index] in _OCR_ADDITIONAL_DIGIT_CONFUSABLES
        and text[index - 1].isalpha()
        and text[index + 1].isalpha()
    }

    mixed_script: set[int] = set()
    token_start: int | None = None
    for index in range(len(text) + 1):
        character = text[index] if index < len(text) else " "
        if character.isalnum():
            if token_start is None:
                token_start = index
            continue
        if token_start is not None:
            token = text[token_start:index]
            if any("A" <= item <= "Z" or "a" <= item <= "z" for item in token):
                mixed_script.update(
                    token_start + offset
                    for offset, item in enumerate(token)
                    if item in _SCRIPT_CONFUSABLES
                )
            token_start = None

    mojibake: set[int] = set()
    for index in range(len(text)):
        for prefix in _MOJIBAKE_PREFIXES:
            if text.startswith(prefix, index):
                mojibake.update(range(index, index + len(prefix)))

    positions = legacy | alpha_confusable | additional_digit_confusable | mixed_script | mojibake
    return positions, {
        "legacy_ligature_or_long_s": len(legacy),
        "alpha_confusable_0_1_vertical_bar": len(alpha_confusable),
        "additional_alpha_confusable_digit_5": len(additional_digit_confusable),
        "mixed_script_confusable": len(mixed_script),
        "mojibake_marker": len(mojibake),
    }


def analyze_text(text: str) -> dict[str, object]:
    """Return deterministic hard-error and review-heuristic metrics for text.

    The result contains hashes and numeric metadata only. It never includes a
    source line or excerpt.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    lines = text.split("\n") if text else []
    normalized_lines = [_normalized_line(line) for line in lines]
    nonempty_lines = [line for line in lines if line.strip()]
    character_count = len(text)
    nonempty_line_count = len(nonempty_lines)

    replacement_count = text.count("\ufffd")
    control_count = sum(
        1
        for character in text
        if unicodedata.category(character) == "Cc" and character not in "\n\r\t"
    )
    private_use_count = sum(1 for character in text if unicodedata.category(character) == "Co")
    soft_hyphen_count = text.count("\u00ad")
    unassigned_or_surrogate_count = sum(
        1 for character in text if unicodedata.category(character) in {"Cn", "Cs"}
    )

    ocr_positions, ocr_breakdown = _suspicious_ocr_positions(text)
    line_end_hyphen_count = sum(
        1
        for line, next_line in zip(lines, lines[1:])
        if len(line.rstrip()) >= 2
        and line.rstrip()[-1] in "-‐‑\u00ad"
        and line.rstrip()[-2].isalpha()
        and bool(next_line.lstrip())
        and next_line.lstrip()[0].islower()
    )
    page_number_count = sum(_is_page_number_candidate(line) for line in nonempty_lines)
    header_footer_count, header_footer_pattern_count = _header_footer_metrics(lines)
    duplicate_count, duplicate_run_count, max_duplicate_run_length = (
        _consecutive_duplicate_line_metrics(normalized_lines)
    )
    recurrent_total, recurrent_excess, recurrent_pattern_count = _global_recurrent_line_metrics(
        normalized_lines
    )
    short_line_count = sum(
        len(line.strip()) <= THRESHOLDS["very_short_line_max_characters"] for line in nonempty_lines
    )
    over_300_line_count = sum(
        len(line.strip()) > THRESHOLDS["line_over_300_characters"] for line in nonempty_lines
    )
    over_1000_line_count = sum(
        len(line.strip()) > THRESHOLDS["line_over_1000_characters"] for line in nonempty_lines
    )
    whitespace_positions = _pathological_whitespace_positions(text)
    excess_blank_lines = _excess_blank_line_count(lines)
    punctuation_positions, punctuation_run_count = _pathological_punctuation_positions(text)

    suspicious_ocr = _measurement(len(ocr_positions), character_count, "character")
    suspicious_ocr["breakdown"] = ocr_breakdown
    header_footer = _measurement(header_footer_count, nonempty_line_count, "nonempty_line")
    header_footer["candidate_pattern_count"] = header_footer_pattern_count
    duplicate_lines = _measurement(duplicate_count, nonempty_line_count, "nonempty_line")
    duplicate_lines["excess_count"] = duplicate_count
    duplicate_lines["run_count"] = duplicate_run_count
    duplicate_lines["max_run_length"] = max_duplicate_run_length
    recurrent_lines = _measurement(recurrent_total, nonempty_line_count, "nonempty_line")
    recurrent_lines["total_occurrences"] = recurrent_total
    recurrent_lines["unique_pattern_count"] = recurrent_pattern_count
    recurrent_lines["excess_count"] = recurrent_excess
    pathological_whitespace = _measurement(len(whitespace_positions), character_count, "character")
    pathological_whitespace["excess_blank_line_count"] = excess_blank_lines
    pathological_punctuation = _measurement(
        len(punctuation_positions), character_count, "character"
    )
    pathological_punctuation["run_count"] = punctuation_run_count

    return {
        "text_sha256": _sha256_text(text),
        "counts": {
            "characters": character_count,
            "non_whitespace_characters": sum(not character.isspace() for character in text),
            "alphanumeric_characters": sum(character.isalnum() for character in text),
            "physical_lines": len(lines),
            "nonempty_lines": nonempty_line_count,
        },
        "hard_errors": {
            "replacement_character": _measurement(replacement_count, character_count, "character"),
            "unexpected_control_character": _measurement(
                control_count, character_count, "character"
            ),
            "private_use_character": _measurement(private_use_count, character_count, "character"),
            "soft_hyphen": _measurement(soft_hyphen_count, character_count, "character"),
            "unassigned_or_surrogate_character": _measurement(
                unassigned_or_surrogate_count, character_count, "character"
            ),
        },
        "review_heuristics": {
            "suspicious_ocr_glyph": suspicious_ocr,
            "line_end_hyphenation": _measurement(
                line_end_hyphen_count, nonempty_line_count, "nonempty_line"
            ),
            "isolated_page_number": _measurement(
                page_number_count, nonempty_line_count, "nonempty_line"
            ),
            "repeated_header_footer": header_footer,
            "consecutive_duplicate_line": duplicate_lines,
            "global_recurrent_line": recurrent_lines,
            "very_short_line": _measurement(short_line_count, nonempty_line_count, "nonempty_line"),
            "line_over_300_characters": _measurement(
                over_300_line_count, nonempty_line_count, "nonempty_line"
            ),
            "line_over_1000_characters": _measurement(
                over_1000_line_count, nonempty_line_count, "nonempty_line"
            ),
            "pathological_whitespace": pathological_whitespace,
            "pathological_punctuation": pathological_punctuation,
        },
    }


def _index_rows(rows: Iterable[Mapping[str, object]], *, label: str) -> dict[str, str]:
    indexed: dict[str, str] = {}
    for row_number, row in enumerate(rows):
        barcode = row.get("barcode")
        text = row.get("text")
        if not isinstance(barcode, str) or not barcode.strip():
            raise ValueError(f"{label} row {row_number} has an invalid barcode")
        if not isinstance(text, str):
            raise ValueError(f"{label} row {row_number} has non-string text")
        barcode = barcode.strip()
        if barcode in indexed:
            raise ValueError(f"{label} contains duplicate barcode {barcode!r}")
        indexed[barcode] = text
    if not indexed:
        raise ValueError(f"{label} contains no rows")
    return indexed


def _require_same_barcodes(
    reference: Mapping[str, object], candidate: Mapping[str, object], *, candidate_label: str
) -> None:
    missing = sorted(set(reference) - set(candidate))
    extra = sorted(set(candidate) - set(reference))
    if missing or extra:
        raise ValueError(
            f"{candidate_label} barcode set differs from raw: missing={missing}, extra={extra}"
        )


def _aggregate_measurements(measurements: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not measurements:
        raise ValueError("cannot aggregate an empty metric set")
    count = sum(int(metric["count"]) for metric in measurements)
    denominator = sum(int(metric["denominator"]) for metric in measurements)
    result = _measurement(count, denominator, str(measurements[0]["denominator_unit"]))

    extra_keys = set().union(*(set(metric) for metric in measurements)) - {
        "count",
        "denominator",
        "denominator_unit",
        "rate",
    }
    for key in sorted(extra_keys):
        values = [metric[key] for metric in measurements if key in metric]
        if key.startswith("max_"):
            result[key] = max(int(value) for value in values)
        elif all(isinstance(value, Mapping) for value in values):
            nested_keys = set().union(*(set(value) for value in values))
            result[key] = {
                nested_key: sum(int(value.get(nested_key, 0)) for value in values)
                for nested_key in sorted(nested_keys)
            }
        else:
            result[key] = sum(int(value) for value in values)
    return result


def _aggregate_stage(analyses: Sequence[tuple[str, Mapping[str, object]]]) -> dict[str, object]:
    if not analyses:
        raise ValueError("cannot aggregate an empty stage")
    text_set_hasher = hashlib.sha256()
    for barcode, analysis in analyses:
        text_set_hasher.update(barcode.encode("utf-8"))
        text_set_hasher.update(b"\0")
        text_set_hasher.update(str(analysis["text_sha256"]).encode("ascii"))
        text_set_hasher.update(b"\0")

    counts = {
        name: sum(int(analysis["counts"][name]) for _, analysis in analyses)
        for name in _RETENTION_FIELDS
    }
    groups: dict[str, object] = {}
    for group_name in ("hard_errors", "review_heuristics"):
        metric_names = analyses[0][1][group_name].keys()
        groups[group_name] = {
            metric_name: _aggregate_measurements(
                [analysis[group_name][metric_name] for _, analysis in analyses]
            )
            for metric_name in metric_names
        }
    return {
        "book_count": len(analyses),
        "text_set_sha256": text_set_hasher.hexdigest(),
        "counts": counts,
        **groups,
    }


def _retention(
    reference: Mapping[str, object], candidate: Mapping[str, object]
) -> dict[str, object]:
    result: dict[str, object] = {}
    for field in _RETENTION_FIELDS:
        reference_count = int(reference["counts"][field])
        candidate_count = int(candidate["counts"][field])
        result[field] = {
            "reference_count": reference_count,
            "candidate_count": candidate_count,
            "delta": candidate_count - reference_count,
            "loss_count": max(0, reference_count - candidate_count),
            "ratio": candidate_count / reference_count if reference_count else None,
        }
    return result


def _metric_count_deltas(
    reference: Mapping[str, object], candidate: Mapping[str, object], group: str
) -> dict[str, int]:
    return {
        metric_name: int(candidate[group][metric_name]["count"])
        - int(reference[group][metric_name]["count"])
        for metric_name in reference[group]
    }


def _comparison(
    reference: Mapping[str, object], candidate: Mapping[str, object]
) -> dict[str, object]:
    reference_hash = reference.get("text_sha256", reference.get("text_set_sha256"))
    candidate_hash = candidate.get("text_sha256", candidate.get("text_set_sha256"))
    retention = _retention(reference, candidate)
    return {
        "changed": reference_hash != candidate_hash,
        "content_loss": any(int(item["loss_count"]) > 0 for item in retention.values()),
        "retention": retention,
        "hard_error_count_delta": _metric_count_deltas(reference, candidate, "hard_errors"),
        "review_heuristic_count_delta": _metric_count_deltas(
            reference, candidate, "review_heuristics"
        ),
    }


def audit_rows(
    raw_rows: Iterable[Mapping[str, object]],
    processed_rows: Iterable[Mapping[str, object]],
    *,
    baseline_rows: Iterable[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Compare raw, processed, and optionally baseline records by barcode."""

    raw = _index_rows(raw_rows, label="raw")
    processed = _index_rows(processed_rows, label="processed")
    _require_same_barcodes(raw, processed, candidate_label="processed")

    raw_analyses = {barcode: analyze_text(raw[barcode]) for barcode in sorted(raw)}
    processed_analyses = {
        barcode: analyze_text(processed[barcode]) for barcode in sorted(processed)
    }
    raw_aggregate = _aggregate_stage(list(raw_analyses.items()))
    processed_aggregate = _aggregate_stage(list(processed_analyses.items()))
    report: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "line_normalization": LINE_NORMALIZATION,
        "detector_parameters": {
            "ocr_alpha_confusable_characters": sorted(_OCR_ALPHA_CONFUSABLES),
            "ocr_additional_digit_confusable_characters": sorted(_OCR_ADDITIONAL_DIGIT_CONFUSABLES),
        },
        "thresholds": THRESHOLDS,
        "book_count": len(raw),
        "aggregate": {
            "raw": raw_aggregate,
            "processed": processed_aggregate,
            "raw_to_processed": _comparison(raw_aggregate, processed_aggregate),
        },
        "books": [
            {
                "barcode": barcode,
                "raw": raw_analyses[barcode],
                "processed": processed_analyses[barcode],
                "raw_to_processed": _comparison(raw_analyses[barcode], processed_analyses[barcode]),
            }
            for barcode in sorted(raw)
        ],
    }

    if baseline_rows is not None:
        baseline = _index_rows(baseline_rows, label="baseline")
        _require_same_barcodes(raw, baseline, candidate_label="baseline")
        baseline_analyses = {
            barcode: analyze_text(baseline[barcode]) for barcode in sorted(baseline)
        }
        baseline_aggregate = _aggregate_stage(list(baseline_analyses.items()))
        baseline_books = [
            {
                "barcode": barcode,
                "baseline_text_sha256": baseline_analyses[barcode]["text_sha256"],
                "candidate_text_sha256": processed_analyses[barcode]["text_sha256"],
                **_comparison(baseline_analyses[barcode], processed_analyses[barcode]),
            }
            for barcode in sorted(raw)
        ]
        report["baseline_diff"] = {
            "aggregate": _comparison(baseline_aggregate, processed_aggregate),
            "books_with_content_loss": [
                book["barcode"] for book in baseline_books if book["content_loss"]
            ],
            "books": baseline_books,
        }
    return report


def build_blind_sample_manifest(
    processed_rows: Iterable[Mapping[str, object]],
    *,
    processed_artifact_sha256: str,
    sample_windows: int,
    sample_seed_sha256: str | None = None,
) -> dict[str, object]:
    """Build a detector-independent, reproducible line-window sample manifest."""

    if not re.fullmatch(r"[0-9a-f]{64}", processed_artifact_sha256):
        raise ValueError("processed_artifact_sha256 must be a lowercase SHA256 hex digest")
    if sample_seed_sha256 is None:
        sample_seed_sha256 = processed_artifact_sha256
    elif not re.fullmatch(r"[0-9a-f]{64}", sample_seed_sha256):
        raise ValueError("sample_seed_sha256 must be a lowercase SHA256 hex digest")
    if sample_windows <= 0:
        raise ValueError("sample_windows must be positive")

    processed = _index_rows(processed_rows, label="processed")
    books: list[dict[str, object]] = []
    for barcode in sorted(processed):
        lines = processed[barcode].split("\n")
        nonempty_line_indices = [index for index, line in enumerate(lines) if line.strip()]
        nonempty_count = len(nonempty_line_indices)
        if sample_windows > nonempty_count:
            raise ValueError(
                f"sample_windows={sample_windows} exceeds nonempty lines={nonempty_count} "
                f"for barcode {barcode!r}"
            )

        samples: list[dict[str, object]] = []
        for bin_index in range(sample_windows):
            bin_start = (bin_index * nonempty_count) // sample_windows
            bin_end = ((bin_index + 1) * nonempty_count) // sample_windows
            selection_digest = hashlib.sha256(
                sample_seed_sha256.encode("ascii")
                + b"\0"
                + barcode.encode("utf-8")
                + b"\0"
                + str(bin_index).encode("ascii")
            ).digest()
            offset = int.from_bytes(selection_digest[:8], "big") % (bin_end - bin_start)
            nonempty_ordinal = bin_start + offset
            physical_line_index = nonempty_line_indices[nonempty_ordinal]
            window_start = max(0, physical_line_index - 1)
            window_end = min(len(lines) - 1, physical_line_index + 1)
            window_text = "\n".join(lines[window_start : window_end + 1])
            samples.append(
                {
                    "bin_index": bin_index,
                    "bin_nonempty_ordinal_start": bin_start,
                    "bin_nonempty_ordinal_end_exclusive": bin_end,
                    "selected_nonempty_ordinal": nonempty_ordinal,
                    "physical_line_index": physical_line_index,
                    "window_start_line_index": window_start,
                    "window_end_line_index": window_end,
                    "window_sha256": hashlib.sha256(window_text.encode("utf-8")).hexdigest(),
                }
            )
        books.append(
            {
                "barcode": barcode,
                "physical_line_count": len(lines),
                "nonempty_line_count": nonempty_count,
                "samples": samples,
            }
        )

    return {
        "schema_version": SAMPLE_SCHEMA_VERSION,
        "processed_artifact_sha256": processed_artifact_sha256,
        "sample_seed_sha256": sample_seed_sha256,
        "sample_windows_per_book": sample_windows,
        "line_index_base": 0,
        "books": books,
    }


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_parquet(path: Path) -> list[dict[str, object]]:
    import pandas as pd

    frame = pd.read_parquet(path, columns=["barcode", "text"])
    return frame.to_dict(orient="records")


def _artifact_metadata(path: Path, row_count: int) -> dict[str, object]:
    return {
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "row_count": row_count,
    }


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _sha256_hex(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise argparse.ArgumentTypeError("must be 64 lowercase hexadecimal characters")
    return value


def _write_report(
    report: Mapping[str, object],
    *,
    output: Path | None,
    input_paths: Sequence[Path],
) -> None:
    encoded = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(encoded)
        return

    resolved_output = output.resolve()
    if any(resolved_output == path.resolve() for path in input_paths):
        raise ValueError("output path must not replace an input Parquet")
    with output.open("x", encoding="utf-8") as destination:
        destination.write(encoded)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the non-destructive Parquet quality audit CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, type=Path, help="raw Principia Parquet")
    parser.add_argument("--processed", required=True, type=Path, help="processed candidate Parquet")
    parser.add_argument(
        "--baseline", type=Path, help="optional prior processed Parquet for candidate diff"
    )
    parser.add_argument(
        "--sample-windows",
        type=_positive_int,
        help="opt in to this many deterministic blind windows per book (for example, 64)",
    )
    parser.add_argument(
        "--sample-seed-sha256",
        type=_sha256_hex,
        help="stable sampling seed; valid only with --sample-windows",
    )
    parser.add_argument("--output", type=Path, help="new JSON report path; default is stdout")
    args = parser.parse_args(argv)
    if args.sample_seed_sha256 is not None and args.sample_windows is None:
        parser.error("--sample-seed-sha256 requires --sample-windows")

    raw_rows = _load_parquet(args.raw)
    processed_rows = _load_parquet(args.processed)
    baseline_rows = _load_parquet(args.baseline) if args.baseline is not None else None
    report = audit_rows(raw_rows, processed_rows, baseline_rows=baseline_rows)

    inputs = {
        "raw": _artifact_metadata(args.raw, len(raw_rows)),
        "processed": _artifact_metadata(args.processed, len(processed_rows)),
    }
    if args.baseline is not None and baseline_rows is not None:
        inputs["baseline"] = _artifact_metadata(args.baseline, len(baseline_rows))
    report["inputs"] = inputs

    if args.sample_windows is not None:
        report["blind_samples"] = build_blind_sample_manifest(
            processed_rows,
            processed_artifact_sha256=str(inputs["processed"]["sha256"]),
            sample_windows=args.sample_windows,
            sample_seed_sha256=args.sample_seed_sha256,
        )

    input_paths = [args.raw, args.processed]
    if args.baseline is not None:
        input_paths.append(args.baseline)
    _write_report(report, output=args.output, input_paths=input_paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
