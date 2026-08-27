# Principia 34 quality qualification

This qualification freezes a reproducible, metadata-only review of the 34 selected
Institutional Books volumes. It does **not** declare the whole collection clean. The
result is one Gold book, fourteen Review books, and nineteen Hold books.

The strict Gold seed is Luther Stearns Cushing's *Manual of Parliamentary Practice*
(`HN6KER`). Its 52,500 Qwen3.8 tokens are useful as a native-context correctness
anchor, but they are not enough to validate a 262k-to-1M context extension. The
near- and over-boundary books still need the targeted work recorded in the
[qualification manifest](../experiments/audits/principia-34-qualification-20260826.json)
before they are used as long-context validation data.

## Frozen artifacts

The data-bearing Parquet files remain outside Git. The repository contains only the
processors, tests, and reports without source excerpts.

| Artifact | SHA-256 | Size | Rows | In Git |
|---|---|---:|---:|---|
| Raw Principia 34 | `af6f864dbacf5151f8735e12ae5f32aedaa81f1c7a126efaeb8539fc65ab4c9f` | 23,768,690 bytes | 34 | No |
| Original `480e5b9` baseline | `08d097cd91f23d901097ffb82f8267797d90463c2ca70329ecce4642cbb22ba7` | 23,132,277 bytes | 34 | No |
| Qualified r8 candidate | `07f9c9a2b29b155077bc8e294fc9ed558c2a3457ce0c08f915174150928e3a87` | 23,111,880 bytes | 34 | No |
| [r8 quality audit](../experiments/audits/principia-34-candidate-quality-20260826-r8.json) | `4343034d4c2f20b616ab5d3148d4a338a2c0318f55fb00802b1418431c4bd928` | 1,376,554 bytes | 34 | Yes |
| [Qualification manifest](../experiments/audits/principia-34-qualification-20260826.json) | `d5aa79aab304c76ade61597557a1cc93f12c29c5130c5eaec30ff1182de5d0fc` | 84,279 bytes | 34 | Yes |

All 34 live handlers reproduce their r8 rows byte-for-byte. The candidate has 34
unique barcodes, 34 unique whole-text hashes, no empty row, and zero aggregate hard
Unicode errors in the five audited classes.

Token counts use the local Qwen3.8-27B tokenizer with `add_special_tokens=False`.
The tokenizer files and their hashes are recorded in the qualification manifest.

| Scope | Books | Tokens |
|---|---:|---:|
| Gold | 1 | 52,500 |
| Review | 14 | 5,196,298 |
| Hold | 19 | 4,827,121 |
| All rows | 34 | 10,075,919 |
| Validation holdouts (Psychology and Federalist) | 2 | 644,361 |
| Non-holdout rows after excluding duplicate Davis 1900 | 31 | 9,036,289 |

The last row is potential coverage after tier-specific repair; it is not a claim that
9.0M tokens are presently training-ready.

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
found 402 actionable windows out of 2,176: 38 header/folio, 137 split, 104 OCR, and
123 layout. These counts are a risk sample, not an estimated semantic error rate.

The tier roster is:

- Gold: Cushing.
- Review: Algebra, Animal Histology, Atonement, Bible as Literature, Channing,
  Student's Chaucer, Dickens, Doctrines of Friends, Evolution of To-day, Mallory,
  Bowen, Mill 1870, Psychology, and Federalist.
- Hold: Church Building, Cornerstone, English Literature, Ethics, Hermeneutical
  Manual, History of Religions, Davis 1900, Davis 1903, Woolsey, Dewey, Emerton,
  Comstock, Whittier, Mill 1884, Leacock, Giddings, Spencer, Stowe, and Bushnell.

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

Mallory is the next closest candidate, but three sampled defects remain: two localized
caption/lexical ordering seams and one sentence-internal punctuation error. Channing
is a 986,686-token near-1M repair candidate, and Chaucer is a 1,150,405-token factor-4
repair candidate. Neither is Gold yet.

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
  --output /path/to/principia-34-candidate-20260826-r8.parquet

python scripts/audit_principia_quality.py \
  --raw experiments/raw/the_principia_34.parquet \
  --processed /path/to/principia-34-candidate-20260826-r8.parquet \
  --baseline /path/to/principia-34-clean-grokken-480e5b9.parquet \
  --sample-windows 64 \
  --sample-seed-sha256 08d097cd91f23d901097ffb82f8267797d90463c2ca70329ecce4642cbb22ba7 \
  --output /tmp/principia-34-quality.json
```

The audit command creates its output exclusively and refuses to overwrite an input.
Compare the resulting hashes with the frozen table above. The qualification builder's
exact invocation is available through `python scripts/build_principia_qualification.py
--help`.
