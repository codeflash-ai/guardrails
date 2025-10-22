# This file contains code adapted from the WordTokenizers.jl
# https://github.com/JuliaText/WordTokenizers.jl project.
# It is subject to the license terms in the Apache License file
# found in the top-level directory of this distribution.
# This file has been modified by Guardrails AI on September 27 2024.

import re


def replace_til_no_change(input_text, pattern, replacement):
    compiled_pattern = re.compile(pattern)
    while True:
        new_text = compiled_pattern.sub(replacement, input_text)
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

    # Precompile separator regex form once
    escaped_separator = re.escape(separator)

    # Precompile regex patterns for efficiency
    patterns = [
        # Breaks sometimes missing after "?", "safe" cases
        (re.compile(r"\b([a-z]+\?)\s+([A-Z][a-z]+)\b"), rf"\1{separator}\2"),
        # Breaks sometimes missing after ".", "safe" cases
        (re.compile(r"\b([a-z]+ \.)\s+([A-Z][a-z]+)\b"), rf"\1{separator}\2"),
        # No breaks producing lines only containing sentence-ending punctuation
        (re.compile(rf"{escaped_separator}([.!?]+){escaped_separator}"), r"\1" + separator),
    ]
    for pat, repl in patterns:
        sentences = pat.sub(repl, sentences)

    # Patterns with replace_til_no_change, use precompiled for efficiency
    til_patterns = [
        (r"\[([^\[\]\(\)]*)" + escaped_separator + r"([^\[\]\(\)]*)\]", r"[\1 \2]"),
        (r"\(([^\[\]\(\)]*)" + escaped_separator + r"([^\[\]\(\)]*)\)", r"(\1 \2)"),
        (r"\[([^\[\]]{0,250})" + escaped_separator + r"([^\[\]]{0,250})\]", r"[\1 \2]"),
        (r"\(([^\(\)]{0,250})" + escaped_separator + r"([^\(\)]{0,250})\)", r"(\1 \2)"),
        (r'"([^"\n]{0,250})' + escaped_separator + r'([^"\n]{0,250})"', r'"\1 \2"'),
        (r"'([^'\n]{0,250})" + escaped_separator + r"([^'\n]{0,250})'", r"'\1 \2'"),
        (
            r"\[((?:[^\[\]]|\[[^\[\]]*\]){0,250})"
            + escaped_separator
            + r"((?:[^\[\]]|\[[^\[\]]*\]){0,250})\]",
            r"[\1 \2]",
        ),
        (
            r"\(((?:[^\(\)]|\([^\(\)]*\)){0,250})"
            + escaped_separator
            + r"((?:[^\(\)]|\([^\(\)]*\)){0,250})\)",
            r"(\1 \2)",
        ),
    ]
    for pat, repl in til_patterns:
        sentences = replace_til_no_change(sentences, pat, repl)

    # Precompiled regex for performance
    sentences = re.sub(
        rf"\.{escaped_separator}([a-z]{{3,}}[a-z-]*[ .:,])", r". \1", sentences
    )

    sentences = re.sub(
        rf"(\b[A-HJ-Z]\.){escaped_separator}", r"\1 ", sentences
    )

    # Precompile regex for coordinating conjunctions
    cc_pattern = re.compile(rf"{escaped_separator}(and|or|but|nor|yet)\s")
    sentences = cc_pattern.sub(lambda m: " " + m.group(1) + " ", sentences)

    # Precompile regexes for prepositions
    # This composite pattern matches any preposition (words are unique, so joining is safe)
    prep_regex_str = "|".join(sorted(prepositions := [
        "of",
        "in",
        "by",
        "as",
        "on",
        "at",
        "to",
        "via",
        "for",
        "with",
        "that",
        "than",
        "from",
        "into",
        "upon",
        "after",
        "while",
        "during",
        "within",
        "through",
        "between",
        "whereas",
        "whether",
    ], key=len, reverse=True))
    prep_pattern = re.compile(rf"{escaped_separator}({prep_regex_str})\s")
    sentences = prep_pattern.sub(lambda m: " " + m.group(1) + " ", sentences)

    # Compile patterns used multiple times in a row for abbreviations
    sentences = re.sub(rf"(\be\.){escaped_separator}(g\.)", r"\1 \2", sentences)
    sentences = re.sub(rf"(\bi\.){escaped_separator}(e\.)", r"\1 \2", sentences)
    sentences = re.sub(rf"(\bi\.){escaped_separator}(v\.)", r"\1 \2", sentences)

    # Precompile all abbreviation patterns with ignorecase for final step
    abbreviations = [
        r"e\. ?g\.",
        r"i\. ?e\.",
        r"i\. ?v\.",
        r"vs\.",
        r"cf\.",
        r"Dr\.",
        r"Mr\.",
        r"Ms\.",
        r"Mrs\.",
        r"Prof\.",
        r"Ph\.?D\.",
        r"Jr\.",
        r"St\.",
        r"Mt\.",
        r"etc\.",
        r"Fig\.",
        r"vol\.",
        r"Vols\.",
        r"no\.",
        r"Nos\.",
        r"et\.",
        r"al\.",
        r"i\. ?v\.",
        r"inc\.",
        r"Ltd\.",
        r"Co\.",
        r"Corp\.",
        r"Dept\.",
        r"est\.",
        r"Asst\.",
        r"approx\.",
        r"dr\.",
        r"fig\.",
        r"mr\.",
        r"mrs\.",
        r"ms\.",
        r"prof\.",
        r"rep\.",
        r"jr\.",
        r"sen\.",
        r"st\.",
        r"vs\.",
        r"i\. ?e\.",
    ]
    # Use a single regex for all abbreviations to reduce number of calls
    abbr_regex_str = "|".join(abbreviations)
    abbr_pattern = re.compile(rf"(\b(?:{abbr_regex_str})){escaped_separator}", flags=re.IGNORECASE)
    sentences = abbr_pattern.sub(r"\1", sentences)

    return sentences


def split_sentences(text, separator="abcdsentenceseperatordcba"):
    # Use the separator in the regex
    text = re.sub(r"([?!.])(?=\s|$)", rf"\1{separator}", text)
    text = postproc_splits(text, separator)
    return re.split(rf"\n?{separator} ?\n?", text)
