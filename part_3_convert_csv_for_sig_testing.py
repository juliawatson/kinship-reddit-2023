from __future__ import annotations
import pandas as pd
import os
from scipy.stats import entropy
from part_2_barplots import create_groups


SIGNIFICANCE_TESTING_DATA_DIR = "data/p_gendered_feminine_regression"

SUBREDDIT_PAIR_TO_CONTRAST = {
    ("AskReddit", "askscience"): "AskReddit",
    ("parenting", "entitledparents"): "parenting"
}


def create_df_from_subreddits(subreddit_files: list[str], p_gendered_feminine_files: list[str]):
    """Attach the values in subreddit_files to a pandas dataframe."""

    # Load the examples
    df = pd.DataFrame()
    for subreddit_file in subreddit_files:
        dataframe = pd.read_csv(subreddit_file)

        # Reset the index so they don't conflict
        dataframe.reset_index(drop=True, inplace=True)
        if "lgbt_baseline" in subreddit_file:
            dataframe["subreddit"] = "lgbt_baseline"
        
        df.reset_index(drop=True, inplace=True)
        df = pd.concat([df, dataframe])

    # Load the p_gendered_feminine data
    p_gendered_feminine_df = pd.DataFrame()
    for file in p_gendered_feminine_files:
        dataframe = pd.read_csv(file)

        # Reset the index so they don't conflict
        dataframe.reset_index(drop=True, inplace=True)
        p_gendered_feminine_df.reset_index(drop=True, inplace=True)

        p_gendered_feminine_df = pd.concat([p_gendered_feminine_df, dataframe])
    p_gendered_feminine_df = p_gendered_feminine_df.drop(columns=["subreddit"])
    p_gendered_feminine_df.reset_index(drop=True, inplace=True)
    df.reset_index(drop=True, inplace=True)

    result = pd.merge(p_gendered_feminine_df, df, on=("id", "index"), how="inner")

    assert len(result) == len(p_gendered_feminine_df)
    return result


def convert_df_to_ints(df, gender_neutral: set, conversion_dict: dict):
    """Return a dataframe with columns [gendered, singular, generic, keys in conversion_dict],
    with each value in gendered being a 1 or 0 and the other columns a 1 or -1.
    """
    df['gendered binary'] = df.apply(lambda row: int(row.kinship_term not in gender_neutral), axis=1)
    df['masc_fem_entropy'] = df.apply(lambda row: entropy([row.p_feminine, 1 - row.p_feminine]), axis=1)

    for key in conversion_dict:
        df[key] = df.apply(conversion_dict[key], axis=1)

    cols_to_keep = ['gendered binary', 'p_gendered', 'masc_fem_entropy', "p_feminine"]
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
    subreddit_contrast = SUBREDDIT_PAIR_TO_CONTRAST[subreddits]
    conversion_dict = {
        f'subreddit_{subreddit_contrast}': lambda row: 1 if row.subreddit.lower() == subreddit_contrast.lower() else 0,
        'kinship_term_child': lambda row: 1 if row.kinship_term in groups['child'] else 0,
        'kinship_term_parent': lambda row: 1 if row.kinship_term in groups['parent'] else 0,
        'kinship_term_partner': lambda row: 1 if row.kinship_term in groups['partner'] else 0,
        'kinship_term_sibling': lambda row: 1 if row.kinship_term in groups['sibling'] else 0,
        'kinship_group': lambda row: get_kinship_group(row.kinship_term, groups),
        'subreddit': lambda row: row.subreddit.lower()
    }  # excludes gendered, singular, and generic, which is consistent across subreddit pairs

    # Identify the files we need
    subreddit_files = []
    for subreddit in subreddits:
        subreddit_files.append(f'data/kinship_terms_csv/{subreddit}.comment.kinship_terms.csv')
    subreddit_str = '_'.join(subreddits)
    p_gendered_feminine_files = []
    for kinship_term_group in ["child", "parent", "partner", "sibling"]:
        p_gendered_feminine_files.append(f'data/p_gendered_feminine/{subreddit_str}_{kinship_term_group}.csv')

    # Use these files to load data; prepare data
    df = create_df_from_subreddits(subreddit_files, p_gendered_feminine_files)
    df = convert_df_to_ints(df, gender_neutral, conversion_dict)
    
    # write file to SIGNIFICANCE_TESTING_DATA_DIR
    df.to_csv(f'{SIGNIFICANCE_TESTING_DATA_DIR}/{subreddit_str}.sig_test.csv', index=False)


if __name__ == "__main__":
    if not os.path.exists(SIGNIFICANCE_TESTING_DATA_DIR):
        os.makedirs(SIGNIFICANCE_TESTING_DATA_DIR)

    groups, gender_neutral, _ = create_groups('terms.csv')

    subreddit_pairs = [("AskReddit", "askscience"), ("parenting", "entitledparents")]

    for subreddit_pair in subreddit_pairs:
        convert_generic_subreddit_pair(subreddit_pair, groups, gender_neutral)
