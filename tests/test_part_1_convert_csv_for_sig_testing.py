import pandas as pd
import pytest
import parts_1_2_convert_csv_for_sig_testing
from part_1_barplots import create_groups


groups, gender_neutral, _ = create_groups('../terms.csv')
kin_terms = groups['child'].union(groups['parent'])


def test_create_df_from_subreddits():
    actual = parts_1_2_convert_csv_for_sig_testing.create_df_from_subreddits(
        ['test_create_df_from_subreddits_input.csv'], kin_terms)
    actual = actual.reset_index(drop=True)  # renumbering the indices
    expected = pd.read_csv('test_create_df_from_subreddits_output.csv')
    assert actual.equals(expected)


def test_convert_df_to_ints_parenting():
    df = pd.read_csv('test_create_df_from_subreddits_output.csv')
    conv = {
        'subreddit_entitledparents': lambda row: 1 if row.subreddit.lower() == 'entitledparents' else 0,
        'kinship_term_parent': lambda row: 1 if row.kinship_term in groups['parent'] else 0,
    }  # used dictionary for parenting/entitledparents
    df = parts_1_2_convert_csv_for_sig_testing.convert_df_to_ints(df, gender_neutral, conv)
    expected = pd.read_csv('test_convert_df_to_ints_input.csv')
    assert df.equals(expected)


def test_convert_df_to_ints_ask3():
    df = pd.read_csv('test_convert_df_to_ints_ask3_input.csv')
    conv = {
        'subreddit_AskWomen': lambda row: 1 if row.subreddit.lower() == 'askwomen' else 0,
        'subreddit_AskMen': lambda row: 1 if row.subreddit.lower() == 'askmen' else 0,
        'kinship_term_child': lambda row: 1 if row.kinship_term in groups['child'] else 0,
        'kinship_term_parent': lambda row: 1 if row.kinship_term in groups['parent'] else 0,
        'kinship_term_partner': lambda row: 1 if row.kinship_term in groups['partner'] else 0,
        'kinship_term_sibling': lambda row: 1 if row.kinship_term in groups['sibling'] else 0
    }
    df = parts_1_2_convert_csv_for_sig_testing.convert_df_to_ints(df, gender_neutral, conv)
    expected = pd.read_csv('test_convert_df_to_ints_ask3_output.csv')
    assert df.equals(expected)


if __name__ == '__main__':
    pytest.main(['test_part_1_convert_csv_for_sig_testing.py', '-v'])
