from __future__ import annotations
import pandas as pd
import os
from part_1_barplots import create_groups


SIGNIFICANCE_TESTING_DATA_DIR = "data/referential_pragmatic_regression"

# The one we predicted to be more gendered is the contrast
SUBREDDIT_PAIR_TO_CONTRAST = {
    ("AskReddit", "askscience"): "AskReddit",
    ("parenting", "entitledparents"): "parenting"
}


def create_df_from_subreddits(subreddit_files: list[str], kin_terms: set):
    """Attach the values in subreddit_files to a pandas dataframe.
    Dataframe will only contain rows whose kinship term is in kin_terms.
    """
    df = pd.DataFrame()
    for subreddit_file in subreddit_files:
        dataframe = pd.read_csv(subreddit_file)

        if "lgbt_baseline" in subreddit_file:
            dataframe["subreddit"] = "lgbt_baseline"
        df = pd.concat([df, dataframe])

    # remove rows that do not contain a kinship term in kin_terms
    df = df[df['kinship_term'].isin(kin_terms)]
    return df


def convert_df_to_ints(df, gender_neutral: set, conversion_dict: dict):
    """Return a dataframe with columns [gendered, singular, generic, keys in conversion_dict],
    with each value in gendered being a 1 or 0 and the other columns a 1 or -1.
    """
    df['gendered binary'] = df.apply(lambda row: int(row.kinship_term not in gender_neutral), axis=1)
    df['singular sum'] = df.apply(lambda row: 1 if row.singular else -1, axis=1)
    df['specific'] = df.apply(lambda row: 1 if row.specific == "specific" else -1, axis=1)
    for key in conversion_dict:
        df[key] = df.apply(conversion_dict[key], axis=1)
    cols_to_keep = ['gendered binary', 'singular sum', 'specific']
    cols_to_keep.extend(list(conversion_dict.keys()))
    dataframe = df[cols_to_keep]
    dataframe = dataframe.rename(columns={'gendered binary': 'gendered', 'singular sum': 'singular'})
    return dataframe


def get_kinship_group(kinship_term, groups):
    for kinship_group in groups:
        if kinship_term in groups[kinship_group]:
            return kinship_group
    raise ValueError(f"{kinship_term} not in one of the relevant groups: ")


def convert_generic_subreddit_pair(subreddits, groups, gender_neutral):
    assert len(subreddits) == 2
    kin_terms = groups['child'].union(groups['parent'], groups['partner'], groups['sibling'])
    subreddit_contrast = SUBREDDIT_PAIR_TO_CONTRAST[subreddits]
    conversion_dict = {
        f'subreddit_{subreddit_contrast}': lambda row: 1 if row.subreddit.lower() == subreddit_contrast.lower() else 0,
        'kinship_term_child': lambda row: 1 if row.kinship_term in groups['child'] else 0,
        'kinship_term_parent': lambda row: 1 if row.kinship_term in groups['parent'] else 0,
        'kinship_term_partner': lambda row: 1 if row.kinship_term in groups['partner'] else 0,
        'kinship_term_sibling': lambda row: 1 if row.kinship_term in groups['sibling'] else 0,
        'kinship_group': lambda row: get_kinship_group(row.kinship_term, groups)
    }  # excludes gendered, singular, and generic, which is consistent across subreddit pairs

    subreddit_files = []
    for subreddit in subreddits:
        subreddit_files.append(f'data/kinship_terms_csv/{subreddit}.comment.kinship_terms.csv')

    df = create_df_from_subreddits(subreddit_files, kin_terms)
    df = convert_df_to_ints(df, gender_neutral, conversion_dict)
    path_name = '_'.join(subreddits)
    
    # write file to SIGNIFICANCE_TESTING_DATA_DIR
    df.to_csv(f'{SIGNIFICANCE_TESTING_DATA_DIR}/{path_name}.sig_test.csv', index=False) 


if __name__ == "__main__":
    if not os.path.exists(SIGNIFICANCE_TESTING_DATA_DIR):
        os.makedirs(SIGNIFICANCE_TESTING_DATA_DIR)

    groups, gender_neutral, _ = create_groups('terms.csv')

    subreddit_pairs = [("AskReddit", "askscience"), ("parenting", "entitledparents")]

    for subreddit_pair in subreddit_pairs:
        convert_generic_subreddit_pair(subreddit_pair, groups, gender_neutral)
