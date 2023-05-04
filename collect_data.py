import json
import csv
from extract_kinship_terms import valid_text, valid_author
import pandas as pd
from nltk import word_tokenize as wtok
from collections import Counter

TERMS_FILE = 'terms.csv'

OUTPUT_DIR = 'data/'

PARENTING_COMMENT_FILTER = 'Your content may have been automatically removed through auto-moderation or ' \
                           'manually removed by a human moderator.'
ASKSCIENCE_COMMENT_FILTER = 'Thank you for your submission! ' \
                            'Unfortunately, your submission has been removed for the following reason(s):'

SPECIFIC_DETERMINERS = {'my', '\'s'}
MIXED_DETERMINERS = {'your', 'his', 'her', 'their', 'our', 'ur'}
GENERIC_DETERMINERS = {'a', 'the', 'another', 'other', 'no', 'some', 'that', 'these', 'this', 'those'}

subs = ['entitledparents', 'parenting', 'askscience', 'askreddit']


def write_frequency(uni, bi, sub):
    hits = []
    for l in csv.DictReader(open(TERMS_FILE)):
        if l['term'].count(' ') == 0:
            f = uni[l['term']]
        else:
            f = bi[tuple(l['term'].split())]
        hits.append([l['term'], f, 1e6 * f / sum(uni.values())])
    df = pd.DataFrame(hits, columns=['term', 'frequency', 'frequency.per.million'])
    df.to_csv('%s_frequencies.csv' % sub)


if __name__ == "__main__":
    for sub in subs:
        seen_body = set()  # to avoid repeats
        uni, bi = Counter(), Counter()  # track unigram and bigram frequencies
        prev_n_processed = 0  # track n words processed; not strictly necessary
        for l in open('../scripts/reddit_tools/%s_comment.json' % sub):
            j = json.loads(l)
            txt = j['body']
            if valid_author(j['author']) and valid_text(j['body'], j['subreddit']) and txt[:100] not in seen_body:
                seen_body.add(txt[:100])
                txt_tok = wtok(txt)
                uni.update(txt_tok)
                bi.update([(txt_tok[i], txt_tok[i + 1]) for i in range(len(txt_tok) - 1)])

            # for breaking at 1e7 words and printing every 1e6; not strictly necessary
            n_words_processed = sum(uni.values())
            if n_words_processed >= 1e7:
                break
            if n_words_processed // int(1e6) > prev_n_processed // int(1e6):
                print(sub, n_words_processed // int(1e6), 'million')
            prev_n_processed = n_words_processed
        write_frequency(uni, bi, sub)
        print(sub, sum(uni.values()))

# entitledparents 1 million
# entitledparents 2 million
# entitledparents 3 million
# entitledparents 4 million
# entitledparents 5 million
# entitledparents 6 million
# entitledparents 7 million
# entitledparents 8 million
# entitledparents 9 million
# entitledparents 10000051
# parenting 1 million
# parenting 2 million
# parenting 3 million
# parenting 4 million
# parenting 5 million
# parenting 6 million
# parenting 7 million
# parenting 8 million
# parenting 9 million
# parenting 10000076
# askscience 1 million
# askscience 2 million
# askscience 3 million
# askscience 4 million
# askscience 5 million
# askscience 6 million
# askscience 7 million
# askscience 8 million
# askscience 9 million
# askscience 10000086
# askreddit 1 million
# askreddit 2 million
# askreddit 3 million
# askreddit 4 million
# askreddit 5 million
# askreddit 6 million
# askreddit 7 million
# askreddit 8 million
# askreddit 9 million
# askreddit 10000015
