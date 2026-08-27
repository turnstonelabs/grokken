"""
Handler for "The Principles of Pathologic Histology" by Frank B. Mallory (1914).

A medical textbook with 497 figures containing 683 illustrations, 124 in colors.
Published by W. B. Saunders Company.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

# Exact spellings confirmed from the 1914 scan and searchable parallel scans.
# Hyphenated replacements are lexical compounds in this edition, while joined
# replacements are discretionary print-line wraps.  No morphological rule is
# applied outside these observed strings.
_CONFIRMED_LINE_WRAP_REPAIRS = (
    ("obliga-\ntions", "obligations"),
    ("type-\nwriting", "type-writing"),
    ("over-\nuse", "over-use"),
    ("pre-\ndominating", "predominating"),
    ("disen-\ntangle", "disentangle"),
    ("non-\ntoxic", "non-toxic"),
    ("normal-\nlooking", "normal-looking"),
    ("pseudo-\nmuscular", "pseudo-muscular"),
    ("constrict-\ning", "constricting"),
    ("dissem-\ninated", "disseminated"),
    ("grape-\nsugar", "grape-sugar"),
    ("pig-\nmentosa", "pigmentosa"),
    ("pete-\nchial", "petechial"),
    ("bath-\ning", "bathing"),
    ("hemo-\nlyze", "hemolyze"),
    ("preserv-\natives", "preservatives"),
    ("bacterio-\nlogically", "bacteriologically"),
    ("inoculat-\ning", "inoculating"),
    ("cur-\nrents", "currents"),
    ("ele-\nmentary", "elementary"),
    ("twenty-\neighth", "twenty-eighth"),
    ("Leva-\nditi", "Levaditi"),
    ("unsatis-\nfactory", "unsatisfactory"),
    ("acqui-\nsition", "acquisition"),
    ("where-\never", "wherever"),
    ("micro-\nnucleus", "micronucleus"),
    ("fertiliza-\ntion", "fertilization"),
    ("environ-\nments", "environments"),
    ("devia-\ntions", "deviations"),
    ("pearl-\nlike", "pearl-like"),
    ("deli-\ncacy", "delicacy"),
    ("har-\nmonize", "harmonize"),
    ("un-\nsatisfactory", "unsatisfactory"),
    ("improve-\nments", "improvements"),
    ("embryo-\nblastoma", "embryoblastoma"),
    ("young-\nest", "youngest"),
    ("Myxomatous-\nlike", "Myxomatous-like"),
    ("osteo-\nsarcomas", "osteosarcomas"),
    ("intramuscu-\nlarly", "intramuscularly"),
    ("in-\nfantry", "infantry"),
    ("dis-\ncover", "discover"),
    ("undeter-\nmined", "undetermined"),
    ("unde-\ntermined", "undetermined"),
    ("elabo-\nrately", "elaborately"),
    ("nephro-\ngenic", "nephrogenic"),
    ("ento-\nderm", "entoderm"),
    ("trans-\nplantations", "transplantations"),
    ("in-\ncompetence", "incompetence"),
    ("muscle-\nbundles", "muscle-bundles"),
    ("heart-\nfibers", "heart-fibers"),
    ("motor-\nexciting", "motor-exciting"),
    ("ante-\ncedent", "antecedent"),
    ("disadvanta-\ngeous", "disadvantageous"),
    ("endothelial-\ncell", "endothelial-cell"),
    ("fibrino-\npurulent", "fibrino-purulent"),
    ("bronchi-\nectases", "bronchiectases"),
    ("per-\nforate", "perforate"),
    ("under-\nlies", "underlies"),
    ("back-\nground", "background"),
    ("\u041e\u0441\u0441\u0430-\nsionally", "Occasionally"),
    ("hexamethyl-\nenamine", "hexamethylenamine"),
    ("Phos-\nphates", "Phosphates"),
    ("colon-\nlike", "colon-like"),
    ("cas-\ntrated", "castrated"),
    ("mucus-\nsecreting", "mucus-secreting"),
    ("tortu-\nous", "tortuous"),
    ("symmet-\nrical", "symmetrical"),
    ("full-\nfledged", "full-fledged"),
    ("osteochondro-\nfibrosarcoma", "osteochondro-fibrosarcoma"),
    ("ex-\npanded", "expanded"),
    ("child-\nhood", "childhood"),
    ("sim-\nplifies", "simplifies"),
    ("de-\nmand", "demand"),
    ("favor-\ning", "favoring"),
    ("trans-\n\nplanted", "transplanted"),
)
_CONFIRMED_CAPTION_SEAM_REPAIRS = (
    (
        "Regenerative proliferation of fibroblasts is fairly active. Exu-\n\n"
        "Fig. 132. Syphilis. Primary lesion. Two mitoses in wall of blood-vessel. M.\n"
        "dation and regeneration",
        "Regenerative proliferation of fibroblasts is fairly active.\n\n"
        "Fig. 132. Syphilis. Primary lesion. Two mitoses in wall of blood-vessel. M.\n\n"
        "Exudation and regeneration",
    ),
    (
        "days it curls up in its characteristic spiral attitude, becomes ap-\n\n"
        "Fig. 162.-Trichiniasis. Part of a muscle-fiber showing portions necrotic and\n"
        "other portions beginning to regenerate.\n"
        "parently innocuous, and may persist in this condition for years\n"
        "(twenty or more) until death of its host and ingestion of the infected muscle by "
        "another host sets it free to continue the cycle of\n"
        "development.",
        "days it curls up in its characteristic spiral attitude, becomes apparently "
        "innocuous, and may persist in this condition for years\n"
        "(twenty or more) until death of its host and ingestion of the infected muscle by "
        "another host sets it free to continue the cycle of\n"
        "development.\n\n"
        "Fig. 162.-Trichiniasis. Part of a muscle-fiber showing portions necrotic and\n"
        "other portions beginning to regenerate.",
    ),
)


class PathologicHistology(BookProcessor):
    """
    Processor for The Principles of Pathologic Histology.
    """

    barcode = "HC1BZF"
    title = "The Principles of Pathologic Histology"
    author = "Mallory, Frank Burr"
    date = "1914"

    notes = """
    Medical textbook on pathologic histology.

    Known quirks:
    - Many figure references (Fig. 257, etc.)
    - Running headers "PATHOLOGIC HISTOLOGY"
    - Technical/medical terminology
    - Descriptions of microscopic observations
    - Library stamps (Countway Library)
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        whitespace.dehyphenate_attested,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Principles of Pathologic Histology."""
        import regex as re

        # Remove exact book/part running heads when paired with a separate page
        # number. Figure labels and unnumbered medical section headings remain.
        running_headers = (
            "PATHOLOGIC HISTOLOGY",
            "TUMORS",
            "INFLAMMATION",
            "URINARY ORGANS",
            "ORGANS OF CIRCULATION",
            "ORGANS OF DIGESTION",
            "RETROGRADE PROCESSES",
            "INDEX",
            "ORGANS OF THE CENTRAL NERVOUS SYSTEM",
            "ORGANS OF RESPIRATION",
            "BLOOD-MAKING ORGANS",
            "OTHER ORGANS",
            "FEMALE GENITAL ORGANS",
            "ORGANS OF LOCOMOTION",
            "MALE GENITAL ORGANS",
        )
        header = "|".join(re.escape(value) for value in running_headers)
        text = re.sub(
            rf"(?m)^(?:"
            rf"[ \t]*\d{{1,4}}[ \t]*\n(?:[ \t]*\n)?[ \t]*(?:{header})[ \t]*"
            rf"|[ \t]*(?:{header})[ \t]*\n(?:[ \t]*\n)?[ \t]*\d{{1,4}}[ \t]*"
            rf")$",
            "",
            text,
        )
        # Header removal happens after the shared blank-line transform. Fold
        # the newly adjacent blank runs before applying exact boundary fixes.
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Confirmed local word-boundary errors. Figure labels and scientific
        # notation are deliberately not normalized wholesale.
        text = text.replace(
            "tissues showing lesions.\nwhich I had",
            "tissues showing lesions\nwhich I had",
        )
        text = re.sub(r"various in-\n{2,}fluences", "various influences", text)
        text = text.replace("smooth musclecells", "smooth muscle-cells")
        text = text.replace("solitary lymphnodules", "solitary lymph-nodules")
        text = text.replace("Giantcells", "Giant-cells")
        text = text.replace(
            "disappear. Some-\n\nFig. 390.-Pancreas. Concretions in dilated glands.\n"
            "times the hyaline",
            "disappear.\n\nFig. 390.-Pancreas. Concretions in dilated glands.\n\n"
            "Sometimes the hyaline",
        )

        for broken, repaired in _CONFIRMED_LINE_WRAP_REPAIRS:
            text = text.replace(broken, repaired)

        for broken, repaired in _CONFIRMED_CAPTION_SEAM_REPAIRS:
            text = text.replace(broken, repaired)

        # Clear OCR defects from the blind sample.
        text = text.replace("nature goes ahout it", "nature goes about it")
        text = text.replace("Somtimes the organisms", "Sometimes the organisms")
        text = text.replace("cannot be told.\napart", "cannot be told\napart")
        text = text.replace("thin non-vascular, walls", "thin non-vascular walls")
        text = text.replace(
            "In typhoid fever focal lesions like those in the liver and com-\n39\n\n"
            "posed of phagocytic endothelial leukocytes",
            "In typhoid fever focal lesions like those in the liver and composed of "
            "phagocytic endothelial leukocytes",
        )

        # A two-column tumor table was serialized across columns.  Repair only
        # the one row containing a residual false continuation; the parallel
        # scan supplies both complete cell and tumor names.
        text = text.replace(
            "6. Leiomyoblast (smooth muscle- Leiomyoblastoma (leiomyoma, leio-\ncell).",
            "6. Leiomyoblast (smooth muscle-cell).\nLeiomyoblastoma (leiomyoma, leiomyosarcoma).",
        )
        text = text.replace(
            "15. Epithelioblast (epithelial cell).\nmyosarcoma).\nEndothelioblastoma.",
            "15. Epithelioblast (epithelial cell).\nEndothelioblastoma.",
        )

        return re.sub(r"\n{3,}", "\n\n", text).strip()
