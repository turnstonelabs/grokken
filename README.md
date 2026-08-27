# grokken

> *"To understand so thoroughly that the observer becomes part of the observed."*

Deep understanding and transformation of historical texts for training data.

`grokken` is a pipeline for processing OCR'd historical books (1825-1914 era) into clean, structured training data. It handles encoding issues, OCR artifacts, archaic typography, and inconsistent formatting through a composable transform system.

## Installation

```bash
# Install (development)
pip install -e ".[dev]"

# With generation pipeline support
pip install -e ".[dev,generation]"
```

## Quick Start

```bash
# List available book handlers
grokken list

# List books in a collection
grokken list --collection principia

# Show info about a book processor
grokken info --barcode 32044010149714

# Process a single book
grokken process --barcode 32044010149714 --source experiments/raw/principia.parquet

# Process an entire collection
grokken process --collection principia --source data.parquet --output out.jsonl
```

## Architecture

```
grokken/
├── grokken/
│   ├── __init__.py       # Package exports
│   ├── base.py           # BookProcessor base class
│   ├── registry.py       # Auto-discovery of book handlers
│   ├── cli.py            # Command-line interface
│   ├── transforms/       # Reusable transform library
│   │   ├── encoding.py   # UTF-8, mojibake, line endings
│   │   ├── ocr.py        # Misreads, long-s, digit confusion
│   │   ├── typography.py # Ligatures, quotes, dashes, spaces
│   │   ├── structure.py  # Headers, page numbers, chapters
│   │   └── whitespace.py # Dehyphenation, paragraphs
│   ├── outputs/          # Output formatters
│   │   ├── parquet.py    # Intermediate storage
│   │   └── jsonl.py      # Training data with chunking
│   ├── generation/       # Training data generation pipeline
│   │   ├── config.py     # Pydantic configuration models
│   │   ├── generator.py  # Core generation logic
│   │   ├── segmenter.py  # Text segmentation
│   │   ├── prompts.py    # Prompt templates
│   │   ├── schema.py     # Data schemas
│   │   └── providers/    # LLM provider integrations
│   └── books/            # Book-specific handlers
│       └── principia/    # The Principia 34 collection
├── experiments/
│   ├── configs/          # Generation pipeline configs
│   ├── raw/              # Input parquet files (gitignored)
│   └── processed/        # Output files (gitignored)
└── tests/
```

## Design Principles

1. **Transforms as pure functions** - `str -> str`, easy to compose and test
2. **Factory functions for parameterized transforms** - `remove_page_headers(pattern=...)` returns a transform
3. **`post_process()` hook** - Standard transforms for 80% of books, escape hatch for quirks
4. **Registry auto-discovery** - Drop a file in `books/`, it's automatically available

## Core Components

### BookProcessor

Base class for book-specific processing. Subclass and define:

```python
class MyBookProcessor(BookProcessor):
    barcode = "12345678901234"  # HathiTrust barcode
    title = "Book Title"
    author = "Author Name"
    date = "1890"
    notes = "Document quirks here"

    transforms = [
        encoding.normalize_to_utf8,
        typography.fix_ligatures,
        whitespace.dehyphenate,
    ]

    def post_process(self, text: str) -> str:
        # Book-specific cleanup
        return text
```

Key methods:
- `load_raw(source)` - Load from parquet file or DataFrame
- `process(text)` - Apply all transforms
- `run(source)` - Full pipeline: load -> process -> return
- `stats()` - Processing statistics

### Registry

Auto-discovers BookProcessor subclasses in `grokken/books/`:

```python
from grokken.registry import registry

proc_cls = registry.get("32044010149714")           # Get by barcode
processors = registry.get_collection("principia")   # Get by collection
registry.list_barcodes()                             # List all barcodes
```

### Transforms

All transforms are `str -> str` functions:

```python
from grokken.transforms import encoding, ocr, typography, structure, whitespace
```

| Module | Purpose |
|--------|---------|
| `encoding` | UTF-8 normalization, mojibake, line endings |
| `ocr` | Common misreads (rn->m, tbe->the), long-s, digit confusion |
| `typography` | Ligatures (fi, fl), quotes, dashes, spaces |
| `structure` | Headers, page numbers, chapters, footnotes |
| `whitespace` | Dehyphenation, paragraph normalization |

Factory pattern for parameterized transforms:

```python
structure.remove_page_headers(pattern=r"^CHAPTER \d+$")
whitespace.collapse_blank_lines(max_consecutive=2)
```

### Output Formatters

```python
from grokken.outputs import save_parquet, save_jsonl, chunk_for_training

save_parquet(records, "output.parquet")

for example in chunk_for_training(text, barcode, max_chars=16000):
    # {"text": ..., "source": {"barcode": ..., "chunk_index": ...}}
```

### Generation Pipeline

The `grokken.generation` module generates training data from cleaned texts:

- **Segmenter** - Splits long books into coherent segments
- **Generator** - Produces summaries and Q&A pairs via LLM providers
- **SimulatedUser** - Generates follow-up questions for multi-turn training data
- **BookAnalyzer** - Analyzes book structure and content characteristics

Configuration via YAML (see `experiments/configs/` for examples):

```bash
# Generate training data for a book
grokken generate --config experiments/configs/psychology_james.yaml

# Generate for an entire collection
grokken generate --config experiments/configs/principia_collection.yaml
```

Requires `OPENAI_API_KEY` environment variable for LLM provider access.

## Data Flow

```
Raw OCR parquet (from HathiTrust via HuggingFace)
    |
    v
BookProcessor (per-book transforms)
    |
    v
Clean text (parquet)
    |
    v
Generation pipeline (summaries, Q&A)
    |
    v
training_data.jsonl
```

## Adding a New Book Handler

1. Create `grokken/books/<collection>/<book>.py`
2. Subclass `BookProcessor` with required class attributes
3. Define `transforms` list (most use standard transforms)
4. Override `post_process()` for book-specific quirks
5. Import in the collection's `__init__.py`

See `grokken/books/principia/psychology_james.py` for a complete example.

## The Principia 34

The initial collection: 34 foundational works (1825-1914) from the Institutional Books dataset, totaling ~10M tokens.

The table below is the original collection inventory. For the frozen Qwen3.8 token
counts, quality tiers, artifact hashes, and current training gates, see
[Principia 34 quality qualification](docs/principia_quality.md).

| # | Title | Author | Date | Tokens |
|---|-------|--------|------|--------|
| 1 | The Principles of Psychology | William James | 1890 | 401,766 |
| 2 | The Atonement | - | 1859 | 431,559 |
| 3 | Introduction to the History of Religions | Crawford Howell Toy | 1913 | 382,708 |
| 4 | The Works of Charles Dickens | Charles Dickens | 1911 | 245,900 |
| 5 | The Writings of Harriet Beecher Stowe | Harriet Beecher Stowe | 1896 | 196,800 |
| 6 | Principles of Pathologic Histology | Frank Burr Mallory | 1914 | 273,924 |
| 7 | The Works of William E. Channing | William Ellery Channing | 1875 | 1,015,818 |
| 8 | Principles of Animal Histology | Ulric Dahlgren | 1908 | 284,500 |
| 9 | Introduction to Ethics | Theodore Jouffroy | 1840 | 125,105 |
| 10 | Elements of Political Science | Stephen Leacock | 1906 | 162,447 |
| 11 | Principles of Political Economy | John Stuart Mill | 1884 | 279,314 |
| 12 | The Doctrines of Friends | Elisha Bates | 1825 | 142,450 |
| 13 | Principles of Political Economy | John Stuart Mill | 1870 | 287,472 |
| 14 | Complete Poetical Works | John Greenleaf Whittier | 1873 | 306,674 |
| 15 | Manual of Parliamentary Practice | Luther Stearns Cushing | 1877 | 52,699 |
| 16 | The Principles of Sociology | Herbert Spencer | 1895 | 468,403 |
| 17 | Elements of International Law | George B. Davis | 1900 | 375,504 |
| 18 | Introduction to International Law | Theodore Dwight Woolsey | 1879 | 310,560 |
| 19 | A Complete Manual of English Literature | Thomas B. Shaw | 1867 | 434,593 |
| 20 | Elements of International Law | George B. Davis | 1903 | 376,244 |
| 21 | An Introduction to Algebra | Jeremiah Day | 1847 | 168,526 |
| 22 | The Vicarious Sacrifice | Horace Bushnell | 1866 | 213,960 |
| 23 | The Student's Chaucer | Geoffrey Chaucer | 1895 | 1,026,471 |
| 24 | Studies in Logical Theory | John Dewey | 1903 | 182,135 |
| 25 | Church Building | Ralph Adams Cram | 1901 | 59,006 |
| 26 | Hermeneutical Manual | Patrick Fairbairn | 1859 | 294,313 |
| 27 | Introduction to the Middle Ages | Ephraim Emerton | 1888 | 121,928 |
| 28 | The Bible as Literature | Irving Francis Wood | 1914 | 148,609 |
| 29 | Evolution of To-day | H. W. Conn | 1886 | 123,615 |
| 30 | A System of Natural Philosophy | J. L. Comstock | 1835 | 156,861 |
| 31 | Principles of Political Economy | Francis Bowen | 1856 | 312,684 |
| 32 | The Corner-stone | Jacob Abbott | 1830 | 176,690 |
| 33 | The Federalist | Hamilton/Madison/Jay | 1864 | 328,303 |
| 34 | The Elements of Sociology | Franklin Henry Giddings | 1898 | 138,221 |

### By Category

| Category | Books | Tokens |
|----------|-------|--------|
| Philosophy, Psychology, Religion | 10 | 3,366,504 |
| Language and Literature | 6 | 2,359,047 |
| Law | 4 | 1,390,611 |
| Political Science | 5 | 1,094,616 |
| Science | 4 | 733,502 |
| Social Sciences | 2 | 606,624 |
| Medicine | 1 | 273,924 |
| Education | 1 | 121,928 |
| Fine Arts | 1 | 59,006 |

## Testing

```bash
pytest                    # Run all tests
pytest -v                 # Verbose
pytest --cov=grokken      # With coverage
```

## Dependencies

- **pandas** (>=2.0) - DataFrame operations
- **pyarrow** (>=14.0) - Parquet I/O
- **regex** (>=2023.0) - Advanced regex (Unicode support)

Optional (`pip install -e ".[generation]"`):
- **openai** (>=1.50.0) - LLM provider
- **pydantic** (>=2.0) - Configuration validation
- **pyyaml** (>=6.0) - Config file parsing

## Etymology

**grokken** (v.): The past participle of *grok* that Heinlein never wrote.

*"The text has been grokken"* -- it has been understood so deeply that its essence can be extracted and transformed.

## License

[MIT](LICENSE)
