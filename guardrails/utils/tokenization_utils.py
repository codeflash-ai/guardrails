# This file contains code adapted from the WordTokenizers.jl
# https://github.com/JuliaText/WordTokenizers.jl project.
# It is subject to the license terms in the Apache License file
# found in the top-level directory of this distribution.
# This file has been modified by Guardrails AI on September 27 2024.

import re

_QUESTION_SPLIT_RE = re.compile(r"\b([a-z]+\?)\s+([A-Z][a-z]+)\b")

_DOT_SPLIT_RE = re.compile(r"\b([a-z]+ \.)\s+([A-Z][a-z]+)\b")

_DOT_NONUPPERCASE_RE_TEMPLATE = r"\.{sep}([a-z]{{3,}}[a-z-]*[ .:,])"

_SINGLE_LETTER_RE_TEMPLATE = r"(\b[A-HJ-Z]\.){sep}"

_ABBR_REGEXES = [
    re.compile(rf"(\be\.){{sep}}(g\.)"),
    re.compile(rf"(\bi\.){{sep}}(e\.)"),
    re.compile(rf"(\bi\.){{sep}}(v\.)"),
]


def replace_til_no_change(input_text, pattern, replacement):
    while True:
        new_text = re.sub(pattern, replacement, input_text)
        if new_text == input_text:
            break
        input_text = new_text
    return input_text


def postproc_splits(sentences, separator):
    """Applies heuristic rules to repair sentence splitting errors. Developed
    for use as postprocessing for the GENIA sentence splitter on PubMed
    abstracts, with minor tweaks for full-text documents.

    `sentences` should be a string, with line breaks on sentence boundaries.
    Returns a similar string, but more correct.

    Based on
    https://github.com/ninjin/geniass/blob/master/geniass-postproc.pl
    Which is
    (c) 2010 Sampo Pyysalo. No rights reserved, i.e. do whatever you like with this.
    Which draws in part on heuristics included in Yoshimasa Tsuruoka's
    medss.pl script.
    """

    # Remove Windows line endings
    sentences = sentences.replace("\r", "")

    # "?" split, precompiled regex
    sentences = _QUESTION_SPLIT_RE.sub(rf"\1{separator}\2", sentences)
    # "." split, precompiled regex
    sentences = _DOT_SPLIT_RE.sub(rf"\1{separator}\2", sentences)

    # No breaks producing lines only containing sentence-ending punctuation
    sentences = _get_static_re(separator).sub(r"\1" + separator, sentences)

    # No breaks inside parentheses/brackets (complex rules via replace_til_no_change,
    # cannot be precompiled or further optimized safely due to loop and dynamic strings)
    sentences = replace_til_no_change(
        sentences,
        r"\[([^\[\]\(\)]*)" + re.escape(separator) + r"([^\[\]\(\)]*)\]",
        r"[\1 \2]",
    )
    sentences = replace_til_no_change(
        sentences,
        r"\(([^\[\]\(\)]*)" + re.escape(separator) + r"([^\[\]\(\)]*)\)",
        r"(\1 \2)",
    )
    sentences = replace_til_no_change(
        sentences,
        r"\[([^\[\]]{0,250})" + re.escape(separator) + r"([^\[\]]{0,250})\]",
        r"[\1 \2]",
    )
    sentences = replace_til_no_change(
        sentences,
        r"\(([^\(\)]{0,250})" + re.escape(separator) + r"([^\(\)]{0,250})\)",
        r"(\1 \2)",
    )
    sentences = replace_til_no_change(
        sentences,
        r'"([^"\n]{0,250})' + re.escape(separator) + r'([^"\n]{0,250})"',
        r'"\1 \2"',
    )
    sentences = replace_til_no_change(
        sentences,
        r"'([^'\n]{0,250})" + re.escape(separator) + r"([^'\n]{0,250})'",
        r"'\1 \2'",
    )
    sentences = replace_til_no_change(
        sentences,
        r"\[((?:[^\[\]]|\[[^\[\]]*\]){0,250})"
        + re.escape(separator)
        + r"((?:[^\[\]]|\[[^\[\]]*\]){0,250})\]",
        r"[\1 \2]",
    )
    sentences = replace_til_no_change(
        sentences,
        r"\(((?:[^\(\)]|\([^\(\)]*\)){0,250})"
        + re.escape(separator)
        + r"((?:[^\(\)]|\([^\(\)]*\)){0,250})\)",
        r"(\1 \2)",
    )

    # Compile the following regexes just once per function call for performance
    dot_nonuppercase_re = re.compile(_DOT_NONUPPERCASE_RE_TEMPLATE.format(sep=re.escape(separator)))
    sentences = dot_nonuppercase_re.sub(r". \1", sentences)
    single_letter_re = re.compile(_SINGLE_LETTER_RE_TEMPLATE.format(sep=re.escape(separator)))
    sentences = single_letter_re.sub(r"\1 ", sentences)

    # No break before coordinating conjunctions (CC)
    coordinating_conjunctions = ("and", "or", "but", "nor", "yet")
    # Precompile CC regexes for speed
    cc_regexes = [_make_wordbreak_regex(cc, separator) for cc in coordinating_conjunctions]
    for cc_re in cc_regexes:
        sentences = cc_re.sub(r" \1", sentences)

    # No break before prepositions (IN)
    prepositions = [
        "of", "in", "by", "as", "on", "at", "to", "via", "for", "with", "that",
        "than", "from", "into", "upon", "after", "while", "during", "within", "through",
        "between", "whereas", "whether",
    ]
    # Precompile preposition regexes for speed
    prep_regexes = [_make_wordbreak_regex(prep, separator) for prep in prepositions]
    for prep_re in prep_regexes:
        sentences = prep_re.sub(r" \1", sentences)

    # No sentence breaks in the middle of specific abbreviations
    for abbr_re in (_ABBR_REGEXES[0].pattern.replace("{sep}", re.escape(separator)),
                    _ABBR_REGEXES[1].pattern.replace("{sep}", re.escape(separator)),
                    _ABBR_REGEXES[2].pattern.replace("{sep}", re.escape(separator))):
        abbr_re_compiled = re.compile(abbr_re)
        # Patterns are simple, no need for IGNORECASE
        sentences = abbr_re_compiled.sub(r"\1 \2", sentences)

    # No sentence break after specific abbreviations
    abbreviations = [
        r"e\. ?g\.", r"i\. ?e\.", r"i\. ?v\.", r"vs\.", r"cf\.", r"Dr\.", r"Mr\.", r"Ms\.", r"Mrs\.",
        r"Prof\.", r"Ph\.?D\.", r"Jr\.", r"St\.", r"Mt\.", r"etc\.", r"Fig\.", r"vol\.", r"Vols\.",
        r"no\.", r"Nos\.", r"et\.", r"al\.", r"i\. ?v\.", r"inc\.", r"Ltd\.", r"Co\.", r"Corp\.",
        r"Dept\.", r"est\.", r"Asst\.", r"approx\.", r"dr\.", r"fig\.", r"mr\.", r"mrs\.", r"ms\.",
        r"prof\.", r"rep\.", r"jr\.", r"sen\.", r"st\.", r"vs\.", r"i\. ?e\.",
    ]
    # Precompile all abbreviation regexes once per call for performance,
    # ~4x fewer calls to re.sub by building a single pattern
    abbr_joined = r"|".join(abbreviations)
    abbreviations_re = re.compile(rf"(\b(?:{abbr_joined})){re.escape(separator)}", flags=re.IGNORECASE)
    sentences = abbreviations_re.sub(r"\1", sentences)

    return sentences


def split_sentences(text, separator="abcdsentenceseperatordcba"):
    # Use precompiled regex for sentence splitting
    split_regex = re.compile(r"([?!.])(?=\s|$)")
    text = split_regex.sub(rf"\1{separator}", text)
    text = postproc_splits(text, separator)
    # Precompile separator split only once
    sep_split_regex = re.compile(rf"\n?{separator} ?\n?")
    return sep_split_regex.split(text)

# The "no breaks producing lines only containing sentence-ending punctuation"
def _get_static_re(separator: str):
    return re.compile(rf"{separator}([.!?]+){separator}")

# Coordinating conjunctions/prepositions regex helper
def _make_wordbreak_regex(word: str, separator: str):
    return re.compile(rf"{separator}({word}\s)", re.IGNORECASE)
