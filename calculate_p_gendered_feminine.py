"""
Using BERT, calculates p(kinship term in kinship term group) for each kinship term usage. Stores these probabilities in
data/probabilities_specific_singular.

Then, calculates p(gendered | context) and p(feminine | gendered) and saves to data/p_gendered_feminine.
"""

import csv
import pandas as pd
from transformers import BertForMaskedLM, BertTokenizer
import torch
from part_2_barplots import create_groups
from tqdm import tqdm
import os
import json
import collections


TERMS_FILE = 'terms.csv'
MASK_INDEX = 103  # 103 corresponds to [MASK]

OUTPUT_DATA_DIR = "data"
INPUT_DATA_DIR = "data"

# Same across all versions
OUTPUT_DIR_PROBABILITIES = f'{OUTPUT_DATA_DIR}/probabilities_specific_singular'
OUTPUT_DIR_P_GENDERED_FEMININE = f'{OUTPUT_DATA_DIR}/p_gendered_feminine'


# set up model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)
model = BertForMaskedLM.from_pretrained('bert-base-uncased')
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)


def get_masked_indices(tokenized_sentences_masked, mask: torch.tensor):
    """Helper function for run_bert. Return a tensor sentence indices that contain mask, and a tensor of
    wordpiece indices that correspond to where mask was found.
    """
    masked_word_indices = (tokenized_sentences_masked['input_ids'] == mask).nonzero()
    # tensor of [[sentence_index, wordpiece_index]]
    return masked_word_indices[:, 0], masked_word_indices[:, 1]


def get_kinship_term_group(row, groups: dict):
    """Helper function for sort_data.
    """
    for group in groups:
        if row.kinship_term in groups[group]:
            return group
    return ValueError(f"there should be a kinship term group for {row['kinship_term']}")


def get_plural_dict(terms_file: str):
    """Return a dictionary mapping each kinship term to its plural form and a dictionary mapping each kinship term group
    to all kinship terms in the group (not just lemmas, as opposed to plot_extracted_subreddit's create_groups).
    """
    plural_dict, full_groups = {}, collections.defaultdict(set)
    with open(terms_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            if row['lemma'] not in plural_dict and row['lemma'] != row['term']:
                plural_dict[row['lemma']] = row['term']

            full_groups[row['group']].add(row['term'])

    plural_dict['s/o'] = 's/o'  # add s/o separately, because no plural case
    return plural_dict, full_groups


def load_df(file: str, full_groups: dict):
    df = pd.read_csv(file)
    df['group'] = df.apply(lambda row: get_kinship_term_group(row, full_groups), axis=1)
    df = df[df['specific'] == 'specific']
    df = df[df['singular'] == True]
    return df


def construct_probability_dict(kinship_set, sentences_with_mask, masked_word_indices, logits):
    assert len(sentences_with_mask) == len(masked_word_indices)
    term_prob_lst = []
    for i in range(len(sentences_with_mask)):
        term_logits = logits[sentences_with_mask[i], masked_word_indices[i], :]
        term_probabilities = torch.nn.functional.softmax(term_logits, 0)
        term_prob_dict = {
            kinship_term: term_probabilities[tokenizer.vocab[kinship_term]].item()
            for kinship_term in kinship_set
        }
        term_prob_lst.append((sentences_with_mask[i], term_prob_dict))
    return term_prob_lst


def run_bert(subreddit, masked_sentences, sentence_ids, kinship_term_indices, batch_size, mask, kinship_group,
             kinship_set, output_file, header, fieldnames):
    """Get probabilities of masked kinship terms for a particular subreddit/kinship_group combination, performed in
    groups of batch_size. Write to csv file output_file for easy access later.
    """
    with torch.no_grad():
        for idx in tqdm(range(0, (len(masked_sentences) // batch_size) + 1), total=len(masked_sentences) // batch_size):
            # get batch
            masked_batch = masked_sentences[idx * batch_size:min(len(masked_sentences), (idx + 1) * batch_size)]
            id_batch = sentence_ids[idx * batch_size:min(len(sentence_ids), (idx + 1) * batch_size)]
            kinship_indices_batch = kinship_term_indices[idx * batch_size:min(len(sentence_ids),
                                                                              (idx + 1) * batch_size)]

            if masked_batch:
                # actually run bert
                tokenized_sentences = tokenizer.batch_encode_plus(
                    masked_batch, return_tensors='pt', add_special_tokens=True,
                    padding=True, truncation=True)
                tokenized_sentences = tokenized_sentences.to(device)  # put to GPU
                sentences_with_mask, masked_word_indices = get_masked_indices(tokenized_sentences, mask)
                output = model(**tokenized_sentences)
                logits = output["logits"]  # has shape [2, 7, 30522] for [n_sentences, max_sentence_length, vocab_size]

                # extract probability dictionary
                term_prob_list = construct_probability_dict(kinship_set, sentences_with_mask, masked_word_indices,
                                                            logits)

                # write to csv
                header = write_to_csv(term_prob_list, kinship_indices_batch, id_batch, output_file, header, subreddit,
                                      kinship_group, fieldnames)
        print(f"{subreddit} {kinship_group} complete!")


def organize_data(df, kinship_group: str):
    sub_df = df[df['group'] == kinship_group]
    assert len(sub_df) > 0
    if kinship_group == 'partner':
        # remove comments pertaining to 'significant other', 's/o' and 'gf' bc they're not in BERT's tokenizer
        sub_df = remove_partner_terms_from_df(sub_df)
    sub_df['masked_body'] = sub_df.apply(lambda row: mask_body(row), axis=1)

    sentences_masked = list(sub_df['masked_body'])
    sentence_ids = list(sub_df['id'])
    kinship_term_indices = list(sub_df['index'])
    return sentences_masked, sentence_ids, kinship_term_indices


def mask_body(row):
    comment_index = int(row['index'])
    end = comment_index + len(row['kinship_term'])
    # only doing this on [specific, singular] cases, so don't need to get length of plural term
    return row['body'][:comment_index] + '[MASK]' + row['body'][end:]


def remove_partner_terms_from_df(df):
    df = df[df['kinship_term'] != 'significant other']
    df = df[df['kinship_term'] != 'gf']
    return df[df['kinship_term'] != 's/o']


def remove_partner_terms_from_kinship_set(kinship_set: set):
    """The kinship terms 's/o', 'significant other', and 'gf' are not in BERT's Tokenizer vocabulary. Mutate the set
    to avoid running into errors.
    """
    kinship_set.remove('s/o')
    kinship_set.remove('significant other')
    kinship_set.remove('gf')


def write_to_csv(term_prob_list, kinship_indices_batch, id_batch, output_file, header, subreddit, kinship_group,
                 fieldnames):
    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if header:
            writer.writeheader()
        for (sentence_index, prob_dict) in term_prob_list:
            row = {
                'subreddit': subreddit,
                'kinship_group': kinship_group,
                'id': id_batch[sentence_index],
                'index': kinship_indices_batch[sentence_index],
                'group_term_prob': prob_dict
            }
            writer.writerow(row)
    return False


def run_functions(subreddits, kinship_groups, batch_size, groups, mask, full_groups, fieldnames):
    for subreddit_pair in subreddits:
        for kinship_group in kinship_groups:
            s = '_'.join(subreddit_pair)
            output_file = f'{OUTPUT_DIR_PROBABILITIES}/{s}_{kinship_group}.csv'
            if os.path.exists(output_file):
                raise ValueError(f"{output_file} already exists")
            header = True
            kinship_set = groups[kinship_group]
            if 's/o' in kinship_set:   # if s/o in kinship_set, so are the other terms that should be removed
                remove_partner_terms_from_kinship_set(kinship_set)
            for subreddit in subreddit_pair:
                file = f'{INPUT_DATA_DIR}/kinship_terms_csv/{subreddit}.comment.kinship_terms.csv'
                df = load_df(file, full_groups)
                sentences_masked, sentence_ids, kinship_term_indices = organize_data(df, kinship_group)
                run_bert(subreddit, sentences_masked, sentence_ids, kinship_term_indices, batch_size, mask,
                         kinship_group, kinship_set, output_file, header, fieldnames)
                header = False


def convert_csv_to_plot_points(file: str, gender_neutral, masculine, kinship_set, fieldnames, output_file: str):
    df = pd.read_csv(file)
    for key in kinship_set:
        df[key] = df.apply(lambda row: convert_create_kinship_term_col(row, key), axis=1)
    gendered_terms, feminine_terms = [], []
    for col in df.columns:
        if col not in masculine and col not in gender_neutral and col not in fieldnames:
            # if not in gender_neutral AND not in masculine => feminine
            feminine_terms.append(col)
        if col not in gender_neutral and col not in fieldnames:
            # if col not in gender_neutral => col is gendered
            gendered_terms.append(col)
    df['p_gendered'] = df.apply(lambda row: calculate_p_gendered(row, gendered_terms, kinship_set), axis=1)
    df['p_feminine'] = df.apply(lambda row: calculate_p_feminine(row, feminine_terms, gendered_terms), axis=1)
    df = df[['subreddit', 'id', 'index', 'p_gendered', 'p_feminine']]
    # storing id and index just in case need to retrieve data later
    df.to_csv(output_file, index=False)   # save to csv


def convert_create_kinship_term_col(row, key: str):
    """Convert row['group_term_prob'] from str to dict because when reading from csv file to pd.DataFrame, the dict
    is read as a string.
    """
    prob_dict = row['group_term_prob']
    prob_dict = prob_dict.replace('\'', '\"')
    prob_dict = json.loads(prob_dict)
    return prob_dict[key]


def calculate_p_gendered(row, gendered_terms, kinship_set):
    numerator = sum(row[gendered_term] for gendered_term in gendered_terms)
    denominator = sum(row[kinship_term] for kinship_term in kinship_set)
    assert 0 <= numerator / denominator <= 1
    return numerator / denominator


def calculate_p_feminine(row, feminine_terms, gendered_terms):
    numerator = sum(row[feminine_term] for feminine_term in feminine_terms)
    denominator = sum(row[gendered_term] for gendered_term in gendered_terms)
    assert 0 <= numerator / denominator <= 1
    return numerator / denominator


if __name__ == "__main__":
    subreddits = [("AskReddit", "askscience"), ("Parenting", "entitledparents")]
    kinship_groups = {'parent', 'child', 'sibling', 'partner'}
    batch_size = 32
    sample_size = 300
    groups, gender_neutral, masculine = create_groups(TERMS_FILE)
    mask = torch.tensor(MASK_INDEX)
    fieldnames = ['subreddit', 'kinship_group', 'id', 'index', 'group_term_prob']
    _, full_groups = get_plural_dict(TERMS_FILE)

    if not os.path.exists(OUTPUT_DIR_PROBABILITIES):
        os.mkdir(OUTPUT_DIR_PROBABILITIES)
    if not os.path.exists(OUTPUT_DIR_P_GENDERED_FEMININE):
        os.mkdir(OUTPUT_DIR_P_GENDERED_FEMININE)

    # calculate probability of each kinship term
    run_functions(subreddits, kinship_groups, batch_size, groups, mask, full_groups, fieldnames)

    # calculate p(gendered) and p(feminine)
    for subreddit_pair in subreddits:
        for kinship_group in kinship_groups:
            s = '_'.join(subreddit_pair)
            file = f'{OUTPUT_DIR_PROBABILITIES}/{s}_{kinship_group}.csv'  # get csv file
            kinship_set = groups[kinship_group]
            if 's/o' in kinship_set:
                remove_partner_terms_from_kinship_set(kinship_set)

            output_file = f"{OUTPUT_DIR_P_GENDERED_FEMININE}/{s}_{kinship_group}.csv"
            convert_csv_to_plot_points(file, gender_neutral, masculine, kinship_set, fieldnames, output_file)
