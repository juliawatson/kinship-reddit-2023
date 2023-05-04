import pandas as pd
import part_1_barplots
import part_2_barplots
import pytest

GENDER_NEUTRAL = {'sibling', 'child', 'kid', 'grandchild', 'grandkid', 'parent', 'nibling', 'grandparent',
                  'partner', 'spouse', 'significant other', 's/o'}
SIBLING = {'brother', 'sister', 'sibling'}
CHILD = {'child', 'kid', 'son', 'daughter'}
GRANDCHILD = {'grandson', 'granddaughter', 'grandchild', 'grandkid'}
PARENT = {'father', 'mother', 'mum', 'mom', 'dad', 'parent'}
NIBLING = {'niece', 'nephew', 'nibling'}
GRANDPARENT = {'grandfather', 'grandmother', 'grandma', 'grandpa', 'grandparent'}
PARTNER = {'wife', 'husband', 'girlfriend', 'boyfriend', 'gf', 'bf', 'partner', 'spouse', 'significant other', 's/o'}
GROUP = {'sibling': SIBLING, 'child': CHILD, 'grandchild': GRANDCHILD, 'parent': PARENT, 'nibling': NIBLING,
         'grandparent': GRANDPARENT, 'partner': PARTNER}
MASC = {'brother', 'son', 'grandson', 'father', 'dad', 'nephew', 'grandfather', 'grandpa', 'husband', 'boyfriend', 'bf'}


groups, gender_neutral, masculine = part_1_barplots.create_groups('../terms.csv')


def test_create_groups():
    groups, gender_neutral, masculine = part_1_barplots.create_groups('../terms.csv')
    assert groups == GROUP
    assert gender_neutral == GENDER_NEUTRAL
    assert masculine == masculine


def test_aggregate_counts():
    file = 'test_data.csv'
    actual = part_1_barplots.aggregate_counts(file, groups, gender_neutral)
    assert actual == 'test_data.aggregated_data.csv'
    df_actual = pd.read_csv(actual)
    df_expected = pd.read_csv('test_data_result.csv')
    assert df_actual.equals(df_expected)


def test_set_df_index():
    df = pd.read_csv('test_data_result.csv')
    start_expected = 0
    for group in groups:
        g = df[df['group'] == group]
        g = g.dropna()
        g, start = part_2_barplots.set_df_index(g, '[sg, specific]', start_expected)
        assert start == start_expected + 4
        assert list(g.index) == ['+sg spec', '+sg oth', '-sg spec', '-sg oth']
        start_expected += 4


def test_normalize_df():
    df = pd.read_csv('test_data_result.csv')
    expected = pd.read_csv('test_data_normalized.csv')
    start = 0
    for group in groups:
        g = df[df['group'] == group]
        g = g.dropna()
        exp = expected[expected['group'] == group]
        exp = exp[exp['specific'].notna()]
        exp, _ = part_2_barplots.set_df_index(exp, '[sg, specific]', start)
        exp = exp[['gendered %', 'gender-neutral %']]
        g, start = part_2_barplots.set_df_index(g, '[sg, specific]', start)
        g = part_2_barplots.normalize_df(g)
        assert exp.equals(g)


if __name__ == '__main__':
    pytest.main(['test_plot_functions.py', '-v'])
