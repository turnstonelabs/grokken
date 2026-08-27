# Principia 34 quality qualification

This qualification freezes a reproducible, metadata-only review of the 34 selected
Institutional Books volumes. It does **not** declare the whole collection clean. The
result is one Gold book, eleven Review books, and twenty-two Hold books.

The strict Gold seed is Luther Stearns Cushing's *Manual of Parliamentary Practice*
(`HN6KER`). Its 52,500 Qwen3.8 tokens are frozen as a native-context validation
holdout, not training data. It is not enough to validate a 262k-to-1M context
extension. The bounded initial calibration instead uses Bowen, Algebra, and Mallory,
the three sources with zero actionable windows in their refreshed independent audit.
This split and its limits are machine-readable in the
[r10 qualification manifest](../experiments/audits/principia-34-qualification-20260826-r10.json).

## Frozen artifacts

The data-bearing Parquet files remain outside Git. The repository contains only the
processors, tests, and reports without source excerpts.

| Artifact | SHA-256 | Size | Rows | In Git |
|---|---|---:|---:|---|
| Raw Principia 34 | `af6f864dbacf5151f8735e12ae5f32aedaa81f1c7a126efaeb8539fc65ab4c9f` | 23,768,690 bytes | 34 | No |
| Original `480e5b9` baseline | `08d097cd91f23d901097ffb82f8267797d90463c2ca70329ecce4642cbb22ba7` | 23,132,277 bytes | 34 | No |
| Qualified r10 candidate | `9c9fb8bdacc4438ce86103c4a6ac202fca23bd787c2cf990d0cf2e69845e8934` | 23,107,588 bytes | 34 | No |
| [r10 quality audit](../experiments/audits/principia-34-candidate-quality-20260826-r10.json) | `21501257be8e25a8c9db18a04155b7228f577c643729b776d0e96a7e7b9a68de` | 1,376,545 bytes | 34 | Yes |
| [r10 qualification manifest](../experiments/audits/principia-34-qualification-20260826-r10.json) | `9b53fa5a1447b4f2f0f8f4c3864563358e2d2aa617c4ad860320fc74d661a4c6` | 85,665 bytes | 34 | Yes |

All 34 live handlers reproduce their r10 rows byte-for-byte. The candidate has 34
unique barcodes, 34 unique whole-text hashes, no empty row, and zero aggregate hard
Unicode errors in the five audited classes.

Token counts use the local Qwen3.8-27B tokenizer with `add_special_tokens=False`.
The tokenizer files and their hashes are recorded in the qualification manifest.

| Scope | Books | Tokens |
|---|---:|---:|
| Gold | 1 | 52,500 |
| Review | 11 | 3,565,197 |
| Hold | 22 | 6,458,145 |
| All rows | 34 | 10,075,842 |
| Bounded calibration training set | 3 | 761,948 |
| Gold validation holdout | 1 | 52,500 |
| Structurally blocked legacy holdouts | 2 | 644,361 |
| Quarantined column reconstruction | 1 | 986,663 |

Only the three explicitly named calibration roles are presently training-ready, and
only for the bounded initial calibration. Tier alone is not admission to training.

## Qualification policy

- **Gold** requires zero hard errors, an exhaustive disposition of residuals, no
  known material layout or source-order blocker, zero actionable fixed-seed windows,
  deterministic handler parity, and no duplicate leakage.
- **Review** means the output is preservation-safe enough for bounded manual repair,
  but known cleanup remains. Review is not automatic permission to train.
- **Hold** means a material OCR, layout, ordering, or duplication blocker remains.

The detector-independent manual audit selects 64 stable line windows per book using
the baseline SHA-256 as its seed. Findings are assigned one primary category:
header/folio, split word, OCR glyph/punctuation, or layout/other. The final review
found 394 actionable windows out of 2,176: 38 header/folio, 127 split, 106 OCR, and
123 layout. These counts are a risk sample, not an estimated semantic error rate.

The tier roster is:

- Gold: Cushing (validation holdout only).
- Review: Algebra, Animal Histology, Atonement, Bible as Literature, Student's
  Chaucer, Dickens, Doctrines of Friends, Evolution of To-day, Mallory, Bowen,
  and Mill 1870.
- Hold: Church Building, Cornerstone, English Literature, Ethics, Hermeneutical
  Manual, History of Religions, Davis 1900, Davis 1903, Woolsey, Dewey, Emerton,
  Comstock, Whittier, Mill 1884, Leacock, Giddings, Spencer, Stowe, Bushnell,
  Psychology, Federalist, and Channing.

The JSON manifest is canonical for barcodes, text hashes, token counts, roles,
per-book sample counts, and concise dispositions.

## Gold result

Cushing was checked against Project Gutenberg and two independent 1877 scans. The
final row has:

- 210,528 characters, 4,356 physical lines, 4,330 nonempty lines, and 52,500 tokens;
- all 194 source page boundaries reviewed;
- paragraphs 1 through 315, chapters I through XV, 31 sections, and all 25 footnote
  blocks present and ordered;
- 177 conventional header/folio pairs, four inline pairs, and one malformed separator
  pair removed with contextual rules;
- no unresolved word continuation, known running-head artifact, material OCR defect,
  or reading-order blocker; and
- zero actionable findings in the final 64-window audit.

The 15 remaining standalone number-like lines were manually dispositioned as the
title year or legitimate index continuations. Automatic review heuristics therefore
remain signals to inspect, not deletion instructions.

Bowen (307,529 tokens), Algebra (176,544), and Mallory (277,875) each had zero
actionable findings in a refreshed 64-window independent audit. They remain Review,
because a clean sample is weaker evidence than Cushing's whole-book census, but they
are explicitly approved for the bounded 25-to-50-step calibration run. Together they
provide 761,948 tokens and 91 complete per-book, non-overlapping 8K contexts with a
next-token continuation; Mallory also crosses the native 262,144-token boundary.

Channing still has five sampled findings, including evidence of two-column reading
order damage, and is machine-quarantined pending page and column reconstruction.
Psychology and Federalist remain structurally blocked Hold sources. Chaucer remains a
1,150,405-token factor-4 repair candidate. None of these sources may enter the initial
calibration set.

## Why dehyphenation changed

The original broad dehyphenation was intentional Phase 0 triage. Split words were a
dominant error class, and the high-recall pass made that class cheap to surface when
there was not yet time to adjudicate every boundary.

Gold qualification pays the deferred precision cost. Risk-enriched review found
figure-label collisions, lexical compounds, and historical spellings that a blanket
join cannot distinguish. The current policy therefore uses same-book attestation,
authoritative preservation lists, strong frequency dominance only when evidence
supports it, explicit rejected joins, and exact book-local page-seam repairs. For
example, Animal Histology now preserves `muscle-cell` and eight figure-fragment
boundaries while still repairing 24 verified joins; Federalist repairs ten externally
supported residual wraps while preserving the rejected `ar-\n\ncontained` and
`inter-\n\nas` split contexts.

This is a two-stage workflow, not a claim that the Phase 0 choice was accidental:
high-recall triage first, preservation-aware qualification before promotion.

## Shared-transform safeguards

The broad OCR cleanup helpers remain inappropriate for this collection without
book-local evidence:

- Applying `remove_ocr_artifacts` to all raw rows would remove 14,934 characters:
  7,145 punctuation characters, 7,679 isolated-special characters including 1,508
  linefeeds, and 110 repeated-run characters. None of the 34 handlers uses it.
- `fix_digit_letter_confusion` has six raw candidates, four in math-like contexts,
  and would also endanger injected hex or sentinel strings. None of the 34 handlers
  uses it.

The Davis 1900 and 1903 editions are near duplicates: 92.70% normalized long-line
containment and 88.28% exact 25-word-shingle containment (216,089 shared shingles).
Davis 1900 is explicitly `duplicate_excluded`; neither edition is Gold.

## Reproduction

From an environment with Grokken, Pandas/PyArrow, and the Qwen tokenizer installed:

```bash
grokken process \
  --collection principia \
  --source experiments/raw/the_principia_34.parquet \
  --output /path/to/principia-34-candidate-20260826-r10.parquet

python scripts/audit_principia_quality.py \
  --raw experiments/raw/the_principia_34.parquet \
  --processed /path/to/principia-34-candidate-20260826-r10.parquet \
  --baseline /path/to/principia-34-clean-grokken-480e5b9.parquet \
  --sample-windows 64 \
  --sample-seed-sha256 08d097cd91f23d901097ffb82f8267797d90463c2ca70329ecce4642cbb22ba7 \
  --output /tmp/principia-34-quality.json
```

The audit command creates its output exclusively and refuses to overwrite an input.
Compare the resulting hashes with the frozen table above. The qualification builder's
exact invocation is available through `python scripts/build_principia_qualification.py
--help`.
