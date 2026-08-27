"""
Handler for "Manual of Parliamentary Practice" by Luther Stearns Cushing (1877).

A procedural manual on rules of proceeding and debate in deliberative assemblies.
The smallest book in the Principia 34 at ~52k tokens.

Score: 37.9
"""

from hashlib import sha256

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace

# The attestation-based shared transform deliberately leaves words that occur
# only once.  The Project Gutenberg transcription of the same text confirms
# these exact print-line wraps; no prefix/suffix rule is applied more broadly.
_CONFIRMED_LINE_WRAP_REPAIRS = (
    ("ascer-\ntaining", "ascertaining"),
    ("be-\nyond", "beyond"),
    ("exten-\nsions", "extensions"),
    ("perform-\nance", "performance"),
    ("pro-\nvide", "provide"),
    ("num-\nbered", "numbered"),
    ("ap-\nprobation", "approbation"),
    ("allu-\nsion", "allusion"),
    ("sugges-\ntions", "suggestions"),
    ("appro-\npriately", "appropriately"),
    ("improp-\nerly", "improperly"),
    ("re-\ncede", "recede"),
    ("com-\nprehends", "comprehends"),
    ("com-\nmence", "commence"),
    ("dis-\ntributed", "distributed"),
    ("in-\ndications", "indications"),
    ("in-\ncompatibility", "incompatibility"),
    ("Dele-\ngates", "Delegates"),
    ("satis-\nfactorily", "satisfactorily"),
    ("actu-\nally", "actually"),
    ("subsist-\ning", "subsisting"),
    ("ex-\namples", "examples"),
    ("ex-\nample", "example"),
    ("sit-\nuation", "situation"),
    ("adjourn-\nment", "adjournment"),
    ("independ-\nently", "independently"),
    ("evi-\ndently", "evidently"),
    ("direct-\ning", "directing"),
    ("in-\nsert", "insert"),
    ("consist-\ning", "consisting"),
    ("compara-\ntively", "comparatively"),
    ("sepa-\nrating", "separating"),
    ("repro-\nbated", "reprobated"),
    ("mo-\ntions", "motions"),
    ("person-\nality", "personality"),
    ("perempto-\nrily", "peremptorily"),
    ("equiva-\nlents", "equivalents"),
    ("un-\nderstandingly", "understandingly"),
    ("de-\ncline", "decline"),
    ("pro-\nceeding", "proceeding"),
    ("har-\nmony", "harmony"),
    ("diffi-\ndent", "diffident"),
    ("neces-\nsary", "necessary"),
)

_CANONICAL_TITLE = """MANUAL OF PARLIAMENTARY PRACTICE.
RULES
OF
PROCEEDING AND DEBATE
IN
DELIBERATIVE ASSEMBLIES.
BY
LUTHER S. CUSHING.
REVISED BY EDMUND L. CUSHING.
BOSTON:
THOMPSON, BROWN, & COMPANY.
1877.

"""

# The scan interleaves the left and right columns of both contents pages.  This
# is a faithful one-entry-per-line reconstruction from the 1877 contents pages;
# the paragraph ranges, including the variant's advertised additions, are kept.
_CANONICAL_CONTENTS = """TABLE OF CONTENTS.
PARAGRAPH
INTRODUCTION — 1 to 15
CHAPTER I. — OF CERTAIN PRELIMINARY MATTERS — 16 to 25
SECT. I. Quorum — 17 to 19
SECT. II. Rules and Orders — 20 to 22
SECT. III. Time of Meeting — 23
SECT. IV. Principle of Decision — 24, 25
CHAPTER II. — OF THE OFFICERS — 26 to 35
SECT. I. The Presiding Officer — 27 to 30
SECT. II. The Recording Officer — 31 to 35
CHAPTER III. — OF THE RIGHTS AND DUTIES OF MEMBERS — 36 to 42
CHAPTER IV. — OF THE INTRODUCTION OF BUSINESS — 43 to 58
CHAPTER V. — OF MOTIONS IN GENERAL — 59 to 61
CHAPTER VI. — OF MOTIONS TO SUPPRESS — 62 to 67
SECT. I. Previous Question — 63 to 66
SECT. II. Indefinite Postponement — 67
CHAPTER VII. — OF MOTIONS TO POSTPONE — 68 to 72
CHAPTER VIII. — OF MOTIONS TO COMMIT — 73 to 77
CHAPTER IX. — OF MOTIONS TO AMEND — 78 to 133
SECT. I. Division of a Question — 79 to 83
SECT. II. Filling Blanks — 84 to 87
SECT. III. Addition, Separation, Transposition — 88 to 91
SECT. IV. Modification, &c., by the Mover — 92, 93
SECT. V. General Rules relating to Amendments — 94 to 102
SECT. VI. Amendments by striking out — 103 to 112
SECT. VII. Amendments by inserting — 113 to 121
SECT. VIII. Amendments by striking out and inserting — 122 to 127
SECT. IX. Amendments changing the nature of a question — 128 to 133
CHAPTER X. — OF THE ORDER AND SUCCESSION OF QUESTIONS — 134 to 187
SECT. I. Privileged Questions — 136 to 149
Adjournment — 137 to 140
Questions of Privilege — 141
Orders of the Day — 142 to 149
SECT. II. Incidental Questions — 150 to 165
Questions of Order — 151 to 154
Reading of Papers — 155 to 160
Withdrawal of a Motion — 161 to 162
Suspension of a Rule — 163 to 164
Amendment of Amendments — 165
SECT. III. Subsidiary Questions — 166 to 187
Lie on the Table — 171 to 173
Previous Question — 174 to 175
Postponement — 176 to 180
Commitment — 181 to 183
Amendment — 184 to 187
CHAPTER XI. — OF THE ORDER OF PROCEEDING — 188 to 200
CHAPTER XII. — OF ORDER IN DEBATE — 201 to 232
SECT. I. As to the Manner of Speaking — 203 to 208
SECT. II. As to the Matter in Speaking — 209 to 214
SECT. III. As to Times of Speaking — 215 to 219
SECT. IV. As to Stopping Debate — 220 to 222
SECT. V. As to Decorum in Debate — 223 to 226
SECT. VI. As to Disorderly Words — 227 to 232
CHAPTER XIII. — OF THE QUESTION — 233 to 249
CHAPTER XIV. — OF RECONSIDERATION — 250 to 257
CHAPTER XV. — OF COMMITTEES — 258 to 311
SECT. I. Their Nature and Functions — 258 to 262
SECT. II. Their Appointment — 263 to 272
SECT. III. Their Organization, &c. — 273 to 285
SECT. IV. Their Report — 286 to 296
SECT. V. Committee of the Whole — 297 to 311
CONCLUDING REMARKS — 312 to 315
ADDITIONS AND CORRECTIONS — 316 to 340
"""


def _relocate_exact_note(
    text: str,
    *,
    parts: tuple[str, ...],
    after: str,
    note: str,
) -> str:
    """Move one verified page-bottom note after its complete paragraph."""
    if text.count(after) != 1 or any(text.count(part) != 1 for part in parts):
        return text
    for part in parts:
        text = text.replace(f"\n{part}\n", "\n", 1)
    return text.replace(after, f"{after}\n\n{note}", 1)


class ParliamentaryPractice(BookProcessor):
    """
    Processor for Manual of Parliamentary Practice.
    """

    barcode = "HN6KER"
    title = "Manual of Parliamentary Practice: rules of proceeding and debate"
    author = "Cushing, Luther Stearns"
    date = "1877"

    notes = """
    Procedural manual for parliamentary proceedings.

    Known quirks:
    - Numbered sections and rules
    - Legal/procedural language
    - Cross-references between sections
    - Smallest book in collection (~52k tokens)
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
        """Book-specific cleanup for Manual of Parliamentary Practice."""
        import regex as re

        # Facing pages alternate the book title and section title as running
        # heads. Match only the observed title next to its Arabic page number.
        running_headers = (
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
        )
        header = "|".join(re.escape(value) for value in running_headers)
        inline_headers = (
            "Order and Succession of Questions. 87",
            "Appointment of Committees. 155",
            "Organization of Committees. 159",
            "Committee of the Whole. 177",
        )
        inline_header = "|".join(re.escape(value) for value in inline_headers)

        # In the source OCR, every running head is preceded by a page-separator
        # blank run. Consume that separator with the exact head/folio pair so a
        # sentence spanning pages retains a single physical-line boundary.
        text = re.sub(
            rf"(?m)\n{{2,}}(?:"
            rf"\d{{1,4}}[ \t]*\n[ \t]*(?:{header})"
            rf"|(?:{header})[ \t]*\n[ \t]*\d{{1,4}}"
            rf"|(?:{inline_header})"
            rf")[ \t]*\n",
            "\n",
            text,
        )

        # Keep the transform testable on isolated excerpts without relying on
        # their page-separator context. Corpus occurrences use the branch above.
        text = re.sub(
            rf"(?m)^(?:"
            rf"[ \t]*\d{{1,4}}[ \t]*\n(?:[ \t]*\n)?[ \t]*(?:{header})[ \t]*"
            rf"|[ \t]*(?:{header})[ \t]*\n(?:[ \t]*\n)?[ \t]*\d{{1,4}}[ \t]*"
            rf")$",
            "",
            text,
        )
        text = re.sub(rf"(?m)^[ \t]*(?:{inline_header})[ \t]*$", "", text)
        # Header removal happens after the shared blank-line transform. Fold
        # the newly adjacent blank runs before applying exact boundary fixes.
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove only source-verified scan matter.  The front block and the
        # interleaved contents are hash-gated so a near match is preserved for
        # review instead of being silently rewritten.
        front_end = "Entered according to Act of Congress in the year 1844, by\n"
        front_end_at = text.find(front_end)
        if front_end_at >= 0:
            front = text[:front_end_at]
            if sha256(front.encode()).hexdigest() == (
                "2019a143f810ce48a74ac899a71e96c03b2a8b0a77408cafc0c6ffeca6df1ec3"
            ):
                text = _CANONICAL_TITLE + text[front_end_at:]

        text = text.replace(
            "L. S. C.\nBOSTON, Nov. 1, 1844.\n3\n-\n-\n\nADVERTISEMENT TO REVISED EDITION.",
            "L. S. C.\nBOSTON, Nov. 1, 1844.\n\nADVERTISEMENT TO REVISED EDITION.",
        )
        text = text.replace(
            "In its new form it is again commended to the favor\n"
            "of the public.\n5\n\nTABLE OF CONTENTS.",
            "In its new form it is again commended to the favor\n"
            "of the public.\n\nTABLE OF CONTENTS.",
        )

        contents_start = text.find("TABLE OF CONTENTS.\n")
        contents_end_marker = "\nPARLIAMENTARY PRACTICE.\nINTRODUCTION."
        contents_end = text.find(contents_end_marker, contents_start)
        if contents_start >= 0 and contents_end >= 0:
            contents = text[contents_start:contents_end]
            if sha256(contents.encode()).hexdigest() == (
                "c5e2bd4d0e7c4048db04d9a508942e00216a5c17ea407ef8fb5063cfad451ebd"
            ):
                text = text[:contents_start] + _CANONICAL_CONTENTS + text[contents_end:]

        text = text.removesuffix("\nCUSHING'S MANUALT\nREVISED EDITION\n2402432412412AHEZUE\n8")

        # Rejoin two words split around the now-removed verified running heads.
        text = re.sub(r"by rea-\n+son", "by reason", text)
        text = re.sub(r"and inconven-\n+ience", "and inconvenience", text)
        text = text.replace("begining with the largest", "beginning with the largest")

        for broken, repaired in _CONFIRMED_LINE_WRAP_REPAIRS:
            text = text.replace(broken, repaired)

        # Exact page-boundary and OCR reading-order defects confirmed against
        # both independent 1877 scans. Numbered sections and formula symbols
        # remain untouched.
        text = text.replace(
            "The terms \" general consent,' as used in\n"
            "parliamentary practice, denote the unanimous.\nopinion",
            'The terms "general consent," as used in\n'
            "parliamentary practice, denote the unanimous\nopinion",
        )
        text = re.sub(
            r"it is a compendious mode of\n{2,}amendment",
            "it is a compendious mode of\namendment",
            text,
        )
        text = re.sub(r"The accept-\n+ance by the mover", "The acceptance by the mover", text)
        text = re.sub(r"are, fur-\n(?:·\n)?ther instructed", "are, further instructed", text)
        text = text.replace(
            'some other time is mentioned, as 66 to-mor-\nor Monday," and that time is fixed',
            'some other time is mentioned, as "to-morrow"\nor "Monday," and that time is fixed',
        )
        text = re.sub(
            r'and fix the time by a motion and question\.\nrow\n""\n66\n+'
            r"CONCLUDING REMARKS\.",
            "and fix the time by a motion and question.\n\nCONCLUDING REMARKS.",
            text,
        )

        # Page-bottom notes are moved only when the scan placed them inside a
        # sentence or after a later paragraph. Their text and callouts remain.
        text = text.replace(
            "debate, and votes only when the assembly is\nequally divided.\n1\n6.",
            "debate, and votes only when the assembly is\nequally divided.\n6.",
        )
        text = text.replace(
            "members of the\nassembly, and, as such", "members of the\nassembly,¹ and, as such"
        )
        text = _relocate_exact_note(
            text,
            parts=(
                "1 In legislative bodies, the clerk is seldom or never a member, "
                "and in some the presiding officer is not a member; as, for\n"
                "example, in the Senate of the United States, the Senate of New\n"
                "York, and in some other State Senates.",
            ),
            after="debate, and votes only when the assembly is\nequally divided.",
            note=(
                "1 In legislative bodies, the clerk is seldom or never a member, "
                "and in some the presiding officer is not a member; as, for\n"
                "example, in the Senate of the United States, the Senate of New\n"
                "York, and in some other State Senates."
            ),
        )

        text = text.replace("he must rise in his place,' and", "he must rise in his place,¹ and")
        text = _relocate_exact_note(
            text,
            parts=(
                "1 In the House of Representatives of Massachusetts, where\n"
                "each member's seat is regularly assigned to him and numbered, it "
                "has been found useful, in deciding upon the claims\n"
                "of several competitors for the floor, to prefer one who rises in\n"
                "his place, to a member who addresses the speaker from the\n"
                "area, the passage-ways, or the seat of any other member.",
            ),
            after=(
                "thus addressed, calls to the member by his\nname; and the member "
                "may then, but not\nbefore, proceed with his business."
            ),
            note=(
                "1 In the House of Representatives of Massachusetts, where\n"
                "each member's seat is regularly assigned to him and numbered, it "
                "has been found useful, in deciding upon the claims\n"
                "of several competitors for the floor, to prefer one who rises in\n"
                "his place, to a member who addresses the speaker from the\n"
                "area, the passage-ways, or the seat of any other member."
            ),
        )
        text = text.replace("If his\n-\ndecision", "If his\ndecision")
        text = text.replace(
            "subsidiary or incidental motions,' which", "subsidiary or incidental motions,¹ which"
        )

        note_61 = (
            "1 It is usual, in legislative assemblies, to provide by a special\n"
            "rule, both as to the particular motions to be used, and the order\n"
            "in which they may be made. Thus the rule in the House of\n"
            "Representatives of Congress (which is also adopted in the House\n"
            'of Representatives of Massachusetts) is, that "when a question\n'
            "is under debate, no motion shall be received, but to adjourn,\n"
            "to lie on the table, for the previous question, to postpone to a\n"
            "day certain, to commit, to amend, to postpone indefinitely;\n"
            "which several motions shall have precedence in the order in\n"
            'which they are arranged."'
        )
        text = _relocate_exact_note(
            text,
            parts=(
                "1 It is usual, in legislative assemblies, to provide by a special\n"
                "rule, both as to the particular motions to be used, and the order\n"
                "in which they may be made. Thus the rule in the House of\n"
                "Representatives of Congress (which is also adopted in the House\n"
                'of Representatives of Massachusetts) is, that "when a question\n'
                "is under debate, no motion shall be received, but to adjourn,\n"
                "to lie on the table, for the previous question, to postpone to a",
                "day certain, to commit, to amend, to postpone indefinitely;\n"
                "which several motions shall have precedence in the order in\n"
                'which they are arranged."',
            ),
            after="will be taken notice of under the heads of the\nseveral motions.",
            note=note_61,
        )

        note_65 = (
            "1 Mr. Jefferson (Manual, § xxxiv.) considers this extension\n"
            "of the previous question as an abuse. He is of opinion, that\n"
            '"its uses would be as well answered by other more simple\n'
            "parliamentary forms; and therefore it should not be favored,\n"
            'but restricted within as narrow limits as possible." Notwithstanding '
            "this suggestion, however, the use of the previous question, as above "
            "stated, has become so firmly established, that it\n"
            "cannot now be disturbed or unsettled."
        )
        text = text.replace(
            "legislative assemblies of the United\nStates.",
            "legislative assemblies of the United\nStates.¹",
        )
        text = _relocate_exact_note(
            text,
            parts=(note_65,),
            after=(
                "is to leave the main question under debate for\n"
                "the residue of the sitting, unless sooner disposed of by taking "
                "the question, or in some\n"
                "other manner."
            ),
            note=note_65,
        )
        text = text.replace("other manner.\n1\n—————\n——\n-\n66.", "other manner.\n66.")

        note_87 = (
            "1 The above is the rule as laid down by Mr. Jefferson (§ 33),\n"
            "and holds where it is not superseded by a special rule, which is\n"
            "generally the case in our legislative assemblies; as, for example, "
            "in the Senate of the United States, the rule is, that in filling "
            "blanks the largest sum and longest time shall be first put.\n"
            "In the House of Commons, in England, the rule established by\n"
            "usage is, that the smallest sum and the longest time shall be\n"
            "first put."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_87,),
            after="assembly comes to a vote.¹",
            note=note_87,
        )

        text = text.replace("same words with\nothers,' or", "same words with\nothers,¹ or")
        note_122 = (
            '1 Mr. Jefferson (§ xxxv.) says, "The question, if desired, is\n'
            'then to be divided," &c.; but, as he makes no exception of a\n'
            "motion to strike out and insert, when treating of the subject of\n"
            "division, and does not here state it as an exception, he undoubtedly "
            "supposes the division in this case to be made in the regular\n"
            "and usual manner."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_122,),
            after=(
                "of Delegates of Virginia, of which Mr. Jefferson had\n"
                "been a member, the parliamentary form of\n"
                "stating the question was in use."
            ),
            note=note_122,
        )

        note_137 = (
            "1 It is commonly said that a motion to adjourn is always in\n"
            "order, but this is not precisely true. The question of adjournment "
            "can, indeed, be moved repeatedly on the same day, yet,\n"
            "in strictness, not without some intermediate question being\n"
            "proposed, after one motion to adjourn is disposed of, and before the "
            "next motion is made for adjourning; as, for example,\n"
            "an amendment to a pending question, or for the reading of\n"
            "some paper. The reason of this is, that, until some other proceeding "
            "has intervened, the question already decided is the\n"
            "same as that newly moved."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_137,),
            after="place of a question already pending, and\nentitled to be first disposed of.",
            note=note_137,
        )
        note_139 = (
            "1 It is quite common, when the business of a deliberative\n"
            "assembly has been brought to a close, to adjourn the assembly "
            "without day. A better form is to dissolve it; as an adjournment "
            "without day, if we regard the etymology of the word\n"
            "adjourn, is a contradiction in terms."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_139,),
            after="legislative assembly, be equivalent to a dissolution.¹",
            note=note_139,
        )

        note_175 = (
            "1 In the House of Representatives of Massachusetts, as the\n"
            "effect of a negative decision of the previous question is not to\n"
            "remove the principal question from before the house, that question "
            "is still open to postponement, commitment, or amendment,\n"
            "notwithstanding such negative decision."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_175,),
            after="that there is then nothing before it to postpone, commit, or amend.¹",
            note=note_175,
        )
        note_197 = (
            "1 The order of motions, for the disposal of any question, is\n"
            "usually fixed by a special rule, in legislative assemblies. See\n"
            "note to paragraph 61."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_197,),
            after="another, and in what order they are to be\ndecided.¹",
            note=note_197,
        )
        note_201 = (
            "1 An exception to this rule is sometimes made in favor of\n"
            "the mover of a question, who is allowed, at the close of the\n"
            "debate, to reply to the arguments brought against his motion;\n"
            "but this is a matter of favor and indulgence, and not of right."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_201,),
            after="regarding reply as the right of one of the\nparties.¹",
            note=note_201,
        )
        note_204 = (
            "1 Sometimes a member, instead of proposing his motion at\n"
            "first, proceeds with his speech; but in such a case he is liable.\n"
            "to be taken down to order, unless he states that he intends to\n"
            "conclude with a motion, and informs the assembly what that\n"
            "motion is; and then he may be allowed to proceed."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_204,),
            after=(
                "these cases, the determination of the presiding\nofficer may be "
                "overruled by the assembly."
            ),
            note=note_204,
        )
        note_209 = (
            "1 In legislative bodies, it is usual to provide that certain\n"
            "questions, as, for example, to adjourn, to lie on the table, for the\n"
            "previous question, or as to the order of business, shall be decided\n"
            "without debate."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_209,),
            after=(
                "adjourn, which in the legislative assemblies\n"
                "of this country would not generally be considered debatable."
            ),
            note=note_209,
        )
        note_215 = (
            "1 The mover and seconder, if they do not speak to the question at "
            "the time when the motion is made and seconded, have\n"
            "the same right with other members to address the assembly."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_215,),
            after="has, in the course of the debate, changed his\nopinion.",
            note=note_215,
        )
        note_229 = (
            "1 The words, as written down, may be amended so as to\n"
            "conform to what the assembly thinks to be the truth."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_229,),
            after="objection of their being disorderly; or he may\nmake an apology for them.",
            note=note_229,
        )
        text = text.replace(
            "declaration of the presiding officer, then the\npresiding officer",
            "declaration of the presiding officer,¹ then the\npresiding officer",
        )
        note_238 = (
            '1 The most common expression is, "I doubt the vote; " or,\n"That vote is doubted."'
        )
        text = _relocate_exact_note(
            text,
            parts=(note_238,),
            after="in order that the members on the one side and\nthe other may be counted.",
            note=note_238,
        )
        text = text.replace("the other may be counted.\n1\n239.", "the other may be counted.\n239.")
        note_281 = (
            "1 This rule is not applicable, of course, to those cases in\n"
            "which the subject, as well as the form or details of a paper, is\n"
            "referred to the committee."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_281,),
            after="make their opposition as individual members.¹",
            note=note_281,
        )
        note_303 = (
            "1 If the object be to stop debate, that can only be effected in\n"
            "the same manner, unless there is a special rule as to the time\n"
            "of speaking, or to taking a subject out of committee."
        )
        text = _relocate_exact_note(
            text,
            parts=(note_303,),
            after="by means of the previous question.¹",
            note=note_303,
        )
        text = text.replace(
            "sub-committees of their\nown members.", "sub-committees of their\nown members.¹"
        )

        exact_repairs = (
            (
                "those which are of general application,\nwhich it",
                "those which are of general application, or\nwhich it",
            ),
            ("of a mot that the matter", "of a motion that the matter"),
            (
                "to which it relates to signif his consent",
                "to which it relates to signify his consent",
            ),
            ("to insert C E, or\nDE, or C D E.", "to insert C E, or\nD E, or C D E."),
            ("120, There is no precedence", "120. There is no precedence"),
            (
                "121. On a motion to amend by inserting\nSECT. VIII.\na paragraph",
                "121. On a motion to amend by inserting\na paragraph",
            ),
            (
                "will stand if the amendment prevails.\nAMENDMENT BY STRIKING OUT\nAND INSERTING.",
                "will stand if the amendment prevails.\nSECT. VIII. AMENDMENT "
                "BY STRIKING OUT AND INSERTING.",
            ),
            (
                "made to express more clearly\nexpress.\nand definitely the sense "
                "which it is intended to\nHence",
                "made to express more clearly\nand definitely the sense which it is "
                "intended to\nexpress. Hence",
            ),
            (
                "but, if decided the other way, leave\nbefore.\nas\nSECTION I.",
                "but, if decided the other way, leave it as\nbefore.\nSECTION I.",
            ),
            (
                "The same result may\nreached more simply",
                "The same result may be\nreached more simply",
            ),
            ("another secondary motion.\nbe\n169.", "another secondary motion.\n169."),
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
            ("either in reason or parlimentary\nusage", "either in reason or parliamentary\nusage"),
            ("timely interference, to cheek offensive", "timely interference, to check offensive"),
            ("obstruct the ex-\npression", "obstruct the expression"),
            (
                "when before the assembly, none other can bẻ",
                "when before the assembly, none other can be",
            ),
            ("no debate upoù, allowed", "no debate upon, allowed"),
            ("motion for the previo question", "motion for the previous question"),
            (
                "SECTION I. As to the Manner of SpeaKING.",
                "SECTION I. AS TO THE MANNER OF SPEAKING.",
            ),
            ("if the whole.\nbody were obliged", "if the whole\nbody were obliged"),
            ("also on the time.\nwhen the assembly", "also on the time\nwhen the assembly"),
            ("have made some progress therein,'", "have made some progress therein,¹"),
            (
                "votes given in is necessary to a choice. ·",
                "votes given in is necessary to a choice.",
            ),
            (
                "presiding officer of the assembly to remain\nroom",
                "presiding officer of the assembly to remain in the\nroom",
            ),
            (
                "See Reports, Disorderly Words.\nthe\nCOMMITMENT",
                "See Reports, Disorderly Words.\nCOMMITMENT",
            ),
            (
                "contents of, to be known by member presenting\n50.",
                "contents of, to be known by member presenting, 50.",
            ),
            (
                "usually provide for their own amendment,\n21.",
                "usually provide for their own amendment, 21.",
            ),
            ("as to times of, 215\n19.", "as to times of, 215-219."),
        )
        for broken, repaired in exact_repairs:
            text = text.replace(broken, repaired)

        # Exact page-edge glyphs and separator rules, never content-bearing
        # section/table numbers or mathematical symbols.
        page_edge_repairs = (
            ("or add to\n-\nthem", "or add to\nthem"),
            ("– ED.]\n-\n11.", "– ED.]\n11."),
            ("common parliamentary law.\n————————\n-\n12.", "common parliamentary law.\n12."),
            (
                "for the purpose. But\n\n62\n·\nParliamentary Practice.\nthis is a mistake",
                "for the purpose. But\nthis is a mistake",
            ),
            (
                "the resolution passed as amended.\n-\n131.",
                "the resolution passed as amended.\n131.",
            ),
            (
                "intended to bear; so that the friends of it, as it was\n,\nIn "
                "some legislative assemblies",
                "intended to bear; so that the friends of it, as it was\nIn some "
                "legislative assemblies",
            ),
            (
                "former position, unless it has been\nitself disposed of by the "
                "question of order.\n་་\n154.",
                "former position, unless it has been\nitself disposed of by the "
                "question of order.\n154.",
            ),
            (
                "occasions, he is prohibited from doing.\n1\nIn the British Parliament",
                "occasions, he is prohibited from doing.\nIn the British Parliament",
            ),
            (
                "or even to read his own speech\n-\nwhich he has prepared",
                "or even to read his own speech\nwhich he has prepared",
            ),
            ('paper is gone through with.\n"\n193.', "paper is gone through with.\n193."),
            (
                "amendments to be proposed in the assembly\n|\nto the body",
                "amendments to be proposed in the assembly\nto the body",
            ),
            (
                "note to paragraph 61.\n#\nit to the assembly",
                "note to paragraph 61.\nit to the assembly",
            ),
            (
                'could very rarely know whether\n"\nthere might',
                "could very rarely know whether\nthere might",
            ),
            (
                "he should finish his speech sitting.\n1\n1\nCHAPTER XII.",
                "he should finish his speech sitting.\nCHAPTER XII.",
            ),
            ("shall speak more\nI\nthan once", "shall speak more\nthan once"),
            ("who is speaking.\n-\n————\n224.", "who is speaking.\n224."),
            ("answered in the\nI\nnegative", "answered in the\nnegative"),
            (
                "to an inconvenient length; nor\nH\n1\ncan any question",
                "to an inconvenient length; nor\ncan any question",
            ),
            (
                "negative of striking out as\n1\nequivalent",
                "negative of striking out as\nequivalent",
            ),
            ("matters of the same nature.\n-\n259.", "matters of the same nature.\n259."),
            ("intervention of a committee.\n-\n296.", "intervention of a committee.\n296."),
            (
                "without any introductory part.\n-\nSECT. V.",
                "without any introductory part.\nSECT. V.",
            ),
            (
                "and, if this motion prevails, the chairman\n—\nt\nrises",
                "and, if this motion prevails, the chairman\nrises",
            ),
            (
                "by striking out, 94, 103–112.\n181\nAMENDMENT by inserting",
                "by striking out, 94, 103–112.\nAMENDMENT by inserting",
            ),
            (
                'take precedence of all motions but for adjournment, 141.\n"\nwhen settled',
                "take precedence of all motions but for adjournment, 141.\nwhen settled",
            ),
        )
        for broken, repaired in page_edge_repairs:
            text = text.replace(broken, repaired)

        final_exact_repairs = (
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
                "cannot now be disturbed or unsettled.\n1\n—————\n——\n-\n66.",
                "cannot now be disturbed or unsettled.\n66.",
            ),
            (
                "for that purpose. But\n\n62\n·\nParliamentary Practice.\nthis is a mistake",
                "for that purpose. But\nthis is a mistake",
            ),
            (
                "SECT. III. ADDITION, SEPARATION, TRANSPO-\nSITION.\none.\n88.",
                "SECT. III. ADDITION, SEPARATION, TRANSPO-\nSITION.\n88.",
            ),
            (
                "instructions to incorporate them together in\n89.",
                "instructions to incorporate them together in one.\n89.",
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
            (
                "but in such a case he is liable.\nto be taken down",
                "but in such a case he is liable\nto be taken down",
            ),
            ('"That vote is doubted."\n1\n239.', '"That vote is doubted."\n239.'),
            ("interference, to\ncheek offensive", "interference, to\ncheck offensive"),
            ("the previo question, 179.", "the previous question, 179."),
            ("TRANSPO-\nSITION.", "TRANSPOSITION."),
            ("THE EX-\nPRESSION", "THE EXPRESSION"),
        )
        for broken, repaired in final_exact_repairs:
            text = text.replace(broken, repaired)

        # Relocating notes exposes two print-line wraps that were previously
        # separated by note text.
        text = re.sub(r"sup-\n+posed", "supposed", text)
        text = re.sub(r"how-\n+ever", "however", text)

        return re.sub(r"\n{3,}", "\n\n", text).strip()
