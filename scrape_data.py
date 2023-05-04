from datetime import datetime
import json
import sys
import time
import requests
import os
import csv


# This script can be used to scrape words/phrases (in QUERY) from
# a list of subreddits (in SUBREDDITS). The results are stored in json files
# in OUTPUT_DIR.


########### These are the fields you likely want to keep the same ###########

# This is the endpoint that we use the requests library to query.
# Details about the pushshift API and how to query its endpoints are
# here: https://github.com/pushshift/api
PUSHSHIFT_ENDPOINT = 'https://api.pushshift.io/reddit/search/comment/'

# This is the maximum number of comments to scrape for each query.
# (We set it higher than the default of 25, because it's faster).
MAX_RETRIEVED_ELEMENTS = 100

# These are the fields we store for each comment. By default it returns more
# fields than this. We only want to store the fields we really need, since that
# takes up less disk space.
FIELDS = ["body", "author", "subreddit", "created_utc", "id"]


########### These are the fields you likely want to change ###########


# Where to store the data.
OUTPUT_DIR = "data/kinship_terms_json"

# Where terms to search for are stored.
TERMS_FILE = 'terms.csv'

# The list of subreddits to scrape data from.
SUBREDDITS = ["dating", "datingoverthirty"]

# The maximum number of comments to scrape per subreddit.
# This script starts with the most recent comments and works backward.
# Once MAX_POSTS are found for a given subreddit, the script stops scraping.
# When MAX_POSTS is None, all comments from a subreddit are scraped.
MAX_POSTS = 100000


def retrieve_reddit_data(
        sub,
        output_dir=OUTPUT_DIR,
        fields=FIELDS,
        max_posts=MAX_POSTS):
    output_filename = output_dir + '/' + sub + '.comment.kinship_terms.json'
    if os.path.exists(output_filename):
        # This prevents accidentally over-writing existing files.
        raise ValueError('Output filename already exists: ' + output_filename)

    today = datetime.utcnow()
    before_date = int((today - datetime(1970, 1, 1)).total_seconds())

    fields = ",".join(fields)

    terms = construct_query()

    count = 0   # number of comments looked at
    done = False
    total_results_count = None  # total number of comments that can be scraped from this subreddit

    with open(output_filename, 'w') as fout:

        while not done:

            query = PUSHSHIFT_ENDPOINT + \
                '?sort=desc' + \
                '&subreddit=' + sub + \
                '&size=' + str(MAX_RETRIEVED_ELEMENTS) + \
                '&before=' + str(before_date) + \
                '&fields=' + str(fields) + \
                '&q=' + terms

            # We set metadata=true for the first query, so we know the
            # total number of results we could scrape. In later queries we don't
            # set it (defaults to false), because it slows down scraping.
            if total_results_count is None:
                query += "&metadata=true"

            sys.stdout.flush()
            try:
                r = requests.get(query)
            except Exception as e:
                print('exception thrown...' + str(e))
                time.sleep(5)
                continue

            if r.status_code != 200:
                print('bad response code:', r.status_code)
                if r.status_code == 429:
                    time.sleep(5)
                    continue
                continue  # retry

            # record a submission/comment only if it's not empty
            json_output = r.json()

            # check size of results of query
            returned_size = len(json_output['data'])

            for element in json_output['data']:
                if 'created_utc' in element.keys():
                    before_date = element['created_utc']

                # write comments regardless of whether it is valid or not
                count += 1
                json.dump(element, fout)
                fout.write('\n')

            # Use metadata to determine how many results to scrape (only on
            # the first query).
            if total_results_count is None:
                total_results_count = json_output["metadata"]["total_results"]
                if max_posts is None or max_posts > total_results_count:
                    max_posts = total_results_count

            # No more comments to scrape.
            if count >= max_posts or returned_size == 0:
                done = True

            percentage = ((count / max_posts) * 100)
            print('Processed ' + str(count) + ' of ' + str(max_posts) + ' comments ' +
                  str(percentage) + '%; reached ' + str(datetime.utcfromtimestamp(before_date)))
    return count


def construct_query():
    """These are the search terms we want to look for. We can look for multiple
    search terms by joining them with "|" (e.g., "dog|cat" would search for all
    usages of "dog" or "cat"). To scrape both singular and plural, you may need
    to list both forms (e.g., "dog|dogs").
    """
    terms_file = open(TERMS_FILE, 'r')
    reader = csv.DictReader(terms_file)
    terms = ''
    for row in reader:
        term = row['term']
        if ' ' in term.strip():         # if multiple words in one query
            terms += '\"' + term.strip() + '\"|'
        else:
            terms += term.strip() + '|'
    terms = terms[0:len(terms) - 1]     # remove last | from string
    return terms


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    for subreddit in SUBREDDITS:
        retrieve_reddit_data(subreddit)
