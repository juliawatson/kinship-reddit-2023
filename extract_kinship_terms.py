"""For each scraped comment, write to csv file whether the comment is a singular/plural usage, specific/mixed/generic
context. Removes bot comments/authors.

NOTE: extracts for specific/mixed/generic (instead of specific/other). Other scripts will group mixed/generic into the
"other" category.
"""

import regex
import json
import csv
import re
import os

TERMS_FILE = 'terms.csv'

OUTPUT_DIR = 'data/'

PARENTING_COMMENT_FILTER = 'Your content may have been automatically removed through auto-moderation or ' \
                           'manually removed by a human moderator.'
ASKSCIENCE_COMMENT_FILTER = 'Thank you for your submission! ' \
                            'Unfortunately, your submission has been removed for the following reason(s):'

SPECIFIC_DETERMINERS = {'my', '\'s'}
MIXED_DETERMINERS = {'your', 'his', 'her', 'their', 'our', 'ur'}
GENERIC_DETERMINERS = {'a', 'the', 'another', 'other', 'no', 'some', 'that', 'these', 'this', 'those'}


def none_or_empty(text):
    return text is None or len(text) == 0 or text == "[removed]" or text == '[deleted]'


def valid_text(text, subreddit):
    # Right now this checks if the comment is none or empty, but in the future
    # we might want to include other checks.
    if none_or_empty(text):
        return False
    if PARENTING_COMMENT_FILTER in text and subreddit.lower() == 'parenting':
        # The phrase PARENTING_COMMENT_FILTER is common in r/Parenting moderation posts,
        # which often include kinship terms.
        return False
    if (ASKSCIENCE_COMMENT_FILTER in text or 'sister sub' in text) and subreddit.lower() == 'askscience':
        # the phrase "sister sub" is often used in r/AskScience, referring to an associated subreddit,
        # but it has been used a couple times in other contexts (ex. 'sister subspecies'). The moderation comments
        # seem to far outweigh the non-moderation comments, though.
        return False
    return True


def valid_author(author):
    # This helps us exclude comments from bots and users that deleted
    # their accounts.
    if author == "[deleted]":
        return False
    if len(re.findall(r"[Bb][Oo][Tt]$", author)) > 0:
        return False
    if len(re.findall(r"automoderato", author.lower())) > 0:
        return False
    return True


def write_csv_from_json(file: str, query: str):
    """After filtering out bot comments and deleted author comments, write Reddit comments containing
    kinship terms listed in TERMS_FILE in a csv file containing other information such as whether it is considered
     'specific' or whether it is singular.
    """
    output = file[:file.index('.json')] + '.csv'
    if '/kinship_term_json' in output:   # not a test file
        output = output.replace('kinship_term_json', 'kinship_terms_csv')

    data_file = open(output, 'w', encoding="utf-8", newline='')
    csv_writer = csv.DictWriter(data_file, fieldnames=['kinship_term', 'specific', 'singular', 'index', 'author',
                                                       'body', 'created_utc', 'id', 'subreddit', 'determiner'])
    csv_writer.writeheader()

    with open(file, encoding="utf-8") as f:
        for line in f.readlines():
            data = json.loads(line)

            # Check to make sure the text hasn't been removed, and that
            # the comment author isn't a bot (or doesn't post only moderation posts).
            is_valid_body = valid_text(data['body'], data['subreddit'])
            is_valid_author = valid_author(data['author'])
            if is_valid_body and is_valid_author:
                additional_info = extract_from_comment(data['body'], query)
                for info in additional_info:
                    info.pop('text')
                    info.update(data)
                    csv_writer.writerow(info)

    data_file.close()


def get_terms(file):
    """Reads terms from TERMS_FILE to construct a regex search string.

    Current plurals from TERMS_FILE include -s, -ren, and wife/wives. All the singular forms in TERMS_FILE should
    appear before the plural versions. Wife/wives are stored separately in the resulting string instead of something
    like wi(f|v)es?.

    For terms other than wife/wives and s/o, there will be a "kinship_pl" group including the "kinship_term" group and
    any additional characters needed to compose the plural form of the word. The "kinship_term" group is the singular
    version of the word. This strategy will not work for words where the plural is not an "extension" of the singular
    form; for example, "kinship_pl" for wife/wives and s/o will return None (though "kinship_term" will return the word
    in question and will have to be dealt with separately).
    """
    terms_file = open(file, 'r')
    reader = csv.DictReader(terms_file)
    terms = []
    for row in reader:
        kinship_term = row['term'].strip()
        term1 = kinship_term[:len(kinship_term) - 1]
        term2 = kinship_term[:len(kinship_term) - 3]
        if term1 in terms:
            # plural -s
            i = terms.index(term1)
            assert kinship_term[len(kinship_term) - 1] == 's'
            terms[i] = '(^|\s)(?P<kinship_pl>(?P<kinship_term>' + terms[i] + ')s?)($|[\s\.,;:\?!\)])'
        elif term2 in terms:
            # children
            i = terms.index(term2)
            assert kinship_term[len(kinship_term) - 3:len(kinship_term)] == 'ren'
            terms[i] = '(^|\s)(?P<kinship_pl>(?P<kinship_term>' + terms[i] + ')(ren)?)($|[\s\.,;:\?!\)])'
        elif kinship_term != 'wife' and kinship_term != 'wives' and kinship_term != 's/o':  # did not include
            # s/os in terms.csv because didn't think it was popular enough
            # new term
            terms.append(kinship_term)
        else:  # wife, wives, and s/o are stored separately; wife/wives because of the f|v issue
            terms.append('(^|\s)(?P<kinship_term>' + kinship_term + ')($|[\s\.,;:\?!\)])')

    if any('(^|\s)(?P<kinship_' not in term or ')($|[\s\.,;:\?!\)])' not in term for term in terms):
        # throw error if there exists a term that has not been given a regex prefix or suffix;
        # term group not specified as it can have a plural group (most) or only kinship (wife, wives, s/o).
        raise ValueError
    return '|'.join(terms)


def extract_from_comment(sentence, query):
    """Creates a list of dictionaries for the desired kinship terms found in sentence. Terms should be a regex
    query string.
    """
    results = []
    matches = regex.finditer(query, sentence, regex.IGNORECASE)
    for search_result in matches:
        # take plural because largest substring that matters
        term_found = search_result.group("kinship_pl")
        if term_found is None:
            # wife, wives, s/o won't have a plural substring because either plural is not a superset of the singular,
            # or plural form was not included in TERMS_FILE
            term_found = search_result.group("kinship_term")
            first, _ = search_result.span("kinship_term")
        else:
            first, _ = search_result.span("kinship_pl")
        term_found = term_found.lower()

        if term_found == 'wives':  # s/o and wife are singular anyway
            singular = 'wife'
        else:
            singular = search_result.group("kinship_term").lower()

        singularity = determine_singularity(term_found, singular)
        specific, determiner = determine_determiner(first, sentence)
        results.append({'text': sentence, 'kinship_term': singular,
                        'singular': singularity, 'specific': specific, 'index': first, 'determiner': determiner})
    return results


def determine_singularity(term_found: str, singular: str):
    """Determine if a word is the singular version or not.

    Won't work for words like moose.
    """
    if term_found != singular:
        return False
    return True


def determine_determiner(first: int, sentence: str):
    """Using determiners, identify whether this is a specific, mixed, or generic usage of
    the kinship term in question.

    First is the index of the first character of the term in question.

    Cases:
        - correct determiner at start of string
        - correct determiner preceding word
        - word at start of string (no det)
        - det incl. in prev. word (no det)
        - term word incl. inside other word (misspelled maybe?, ex. the cat flew over thebrother)
    """
    for determiner in SPECIFIC_DETERMINERS:  # my or 's
        if determiner == '\'s':
            query_str = f'(?P<det>{determiner})\s'
        else:  # determiner == 'my'
            query_str = f'(^|\s)(?P<det>{determiner})\s'

        for match in regex.finditer(query_str, sentence, regex.IGNORECASE):
            # whiteline (ex. ' ' or '\n') may precede determiner, and a space must succeed it
            start, end = match.span()
            if end == first:  # if determiner + ' ' takes place immediately before term in question
                return 'specific', sentence[start:end].strip()

    for determiner in MIXED_DETERMINERS:
        for match in regex.finditer(f'(^|\s)(?P<det>{determiner})\s', sentence, regex.IGNORECASE):
            # whiteline (ex. ' ' or '\n') may precede determiner, and a space must succeed it
            start, end = match.span()
            if end == first:  # if determiner + ' ' takes place immediately before term in question
                return 'mixed', sentence[start:end].strip()

    for determiner in GENERIC_DETERMINERS:  # additional for-loop to save generic determiners
        for match in regex.finditer(f'(^|\s)(?P<det>{determiner})\s', sentence, regex.IGNORECASE):
            # whiteline (ex. ' ' or '\n') may precede determiner, and a space must succeed it
            start, end = match.span()
            if end == first:  # if determiner + ' ' takes place immediately before term in question
                return 'generic', sentence[start:end].strip()

    return 'generic', ''  # when no determiner preceding word


if __name__ == "__main__":
    subreddits = ["AskReddit", "askscience", "Parenting", "entitledparents"]

    terms = get_terms(TERMS_FILE)

    if not os.path.exists(f"{OUTPUT_DIR}/kinship_terms_csv"):
        os.mkdir(f"{OUTPUT_DIR}/kinship_terms_csv")

    for subreddit in subreddits:
        # this will write a new csv for each subreddit
        filename = f'data/kinship_term_json/{subreddit}.comment.kinship_terms.json'
        write_csv_from_json(filename, terms)
        print(filename + ' was csv\'d!')
