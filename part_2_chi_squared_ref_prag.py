import os
from scipy.stats import chi2_contingency
import pandas as pd


def load_all_comb_data(file, kinship_group):
    df = pd.read_csv(file)
    spec_sg = df[(df['group'] == kinship_group) & (df['specific'] == 'specific') & (df['singular'] == True)].iloc[0]
    spec_sg = spec_sg['gendered'] + spec_sg['gender-neutral']

    spec_pl = df[(df['group'] == kinship_group) & (df['specific'] == 'specific') & (df['singular'] == False)].iloc[0]
    spec_pl = spec_pl['gendered'] + spec_pl['gender-neutral']

    other_sg = df[(df['group'] == kinship_group) & (df['specific'] == 'other') & (df['singular'] == True)].iloc[0]
    other_sg = other_sg['gendered'] + other_sg['gender-neutral']

    other_pl = df[(df['group'] == kinship_group) & (df['specific'] == 'other') & (df['singular'] == False)].iloc[0]
    other_pl = other_pl['gendered'] + other_pl['gender-neutral']
    return [spec_sg, spec_pl, other_sg, other_pl]


def load_spec_sg_vs_other(file, kinship_group):
    df = pd.read_csv(file)
    spec_sg = df[(df['group'] == kinship_group) & (df['specific'] == 'specific') & (df['singular'] == True)].iloc[0]
    spec_sg = spec_sg['gendered'] + spec_sg['gender-neutral']

    rest = df[(df['group'] == kinship_group) & (df['specific'].isnull()) & (df['singular'].isnull())].iloc[0]
    rest = rest['gendered'] + rest['gender-neutral'] - spec_sg

    return [spec_sg, rest]


def load_spec_vs_other(file, kinship_group):
    df = pd.read_csv(file)
    spec = df[(df['group'] == kinship_group) & (df['specific'] == 'specific')].sum()
    spec = spec['gendered'] + spec['gender-neutral']

    rest = df[(df['group'] == kinship_group) & (df['specific'].isnull()) & (df['singular'].isnull())].sum()
    rest = rest['gendered'] + rest['gender-neutral'] - spec

    return [spec, rest], ["specific", "other"]


def load_singular_vs_plural(file, kinship_group):
    df = pd.read_csv(file)
    singular = df[(df['group'] == kinship_group) & (df['singular'] == True)].sum()
    singular = singular['gendered'] + singular['gender-neutral']

    rest = df[(df['group'] == kinship_group) & (df['specific'].isnull()) & (df['singular'].isnull())].sum()
    rest = rest['gendered'] + rest['gender-neutral'] - singular

    return [singular, rest], ["singular", "plural"]


def run_functions(kinship_groups, subreddit_pairs, function):
    for subreddit_pair in subreddit_pairs:
        s = '_'.join(subreddit_pair)
        ref_prag_statistics = pd.DataFrame(columns=['kinship_group', 'type', 'chi_squared_statistic', 'p_value'])

        for kinship_group in kinship_groups:
            data = []
            for subreddit in subreddit_pair:
                file = f"data/aggregated_data/{subreddit}.comment.kinship_terms.aggregated_data.csv"
                curr_row, column_names = function(file, kinship_group)
                data.append(curr_row)
            
            df = pd.DataFrame(
                data, 
                columns=column_names, 
                index=subreddit_pair)
            df["total"] = 0
            for colname in column_names:
                df["total"] += df[colname]
            for colname in column_names:
                df[f"{colname}_normalized"] = df[colname] / df["total"]
            print(kinship_group)
            print(df)
            print("\n\n")

            statistic, p_value, _, _ = chi2_contingency(data)
            # if p_value_rest == 0 or p_value_all == 0:
            #     print(kinship_groups)
            label = "_vs_".join(column_names)
            ref_prag_statistics.loc[len(ref_prag_statistics)] = [kinship_group, label, statistic, p_value]

        output_file = f'data/chi_squared/ref_prag/{s}.{label}.csv'
        ref_prag_statistics = ref_prag_statistics.sort_values(by='type')
        ref_prag_statistics.to_csv(output_file, index=False)
        print(f"{s} complete!")


if __name__ == "__main__":
    kinship_groups = {'parent', 'sibling', 'child', 'partner'}
    subreddit_pairs = [('Parenting', 'entitledparents'), ('AskReddit', 'askscience')]

    if not os.path.exists('data/chi_squared'):
        os.mkdir('data/chi_squared')

    if not os.path.exists('data/chi_squared/ref_prag'):
        os.mkdir('data/chi_squared/ref_prag')

    run_functions(kinship_groups, subreddit_pairs, load_spec_vs_other)
    run_functions(kinship_groups, subreddit_pairs, load_singular_vs_plural)


# Specific vs. other
    # sibling
    #                  specific  other  total  specific_normalized  other_normalized
    # Parenting            2582   6108   8690             0.297123          0.702877
    # entitledparents      5115  13240  18355             0.278671          0.721329



    # partner
    #                  specific  other  total  specific_normalized  other_normalized
    # Parenting           11828  14917  26745             0.442251          0.557749
    # entitledparents      3743   9465  13208             0.283389          0.716611



    # parent
    #                  specific  other  total  specific_normalized  other_normalized
    # Parenting           12416  51989  64405             0.192780          0.807220
    # entitledparents     21593  77659  99252             0.217557          0.782443



    # child
    #                  specific   other   total  specific_normalized  other_normalized
    # Parenting           29886  106233  136119             0.219558          0.780442
    # entitledparents      6791   67078   73869             0.091933          0.908067



    # sibling
    #             specific  other  total  specific_normalized  other_normalized
    # AskReddit       6839   8440  15279             0.447608          0.552392
    # askscience      1761   7222   8983             0.196037          0.803963



    # partner
    #             specific  other  total  specific_normalized  other_normalized
    # AskReddit      12786  15608  28394             0.450306          0.549694
    # askscience      3584   7332  10916             0.328325          0.671675



    # parent
    #             specific  other  total  specific_normalized  other_normalized
    # AskReddit      25850  27500  53350             0.484536          0.515464
    # askscience      6566  34542  41108             0.159726          0.840274



    # child
    #             specific  other  total  specific_normalized  other_normalized
    # AskReddit       4874  51384  56258             0.086637          0.913363
    # askscience      3184  58497  61681             0.051620          0.948380


# Singular vs. plural

    # sibling
    #                  singular  plural  total  singular_normalized  plural_normalized
    # Parenting            6425    2265   8690             0.739356           0.260644
    # entitledparents     14388    3967  18355             0.783874           0.216126



    # partner
    #                  singular  plural  total  singular_normalized  plural_normalized
    # Parenting           25454    1291  26745             0.951729           0.048271
    # entitledparents     12412     796  13208             0.939733           0.060267



    # parent
    #                  singular  plural  total  singular_normalized  plural_normalized
    # Parenting           42544   21861  64405             0.660570           0.339430
    # entitledparents     69979   29273  99252             0.705064           0.294936



    # child
    #                  singular  plural   total  singular_normalized  plural_normalized
    # Parenting           77683   58436  136119             0.570699           0.429301
    # entitledparents     40268   33601   73869             0.545127           0.454873



    # sibling
    #             singular  plural  total  singular_normalized  plural_normalized
    # AskReddit      11774    3505  15279             0.770600           0.229400
    # askscience      5304    3679   8983             0.590449           0.409551



    # partner
    #             singular  plural  total  singular_normalized  plural_normalized
    # AskReddit      26299    2095  28394             0.926217           0.073783
    # askscience      8680    2236  10916             0.795163           0.204837



    # parent
    #             singular  plural  total  singular_normalized  plural_normalized
    # AskReddit      37909   15441  53350             0.710572           0.289428
    # askscience     27975   13133  41108             0.680524           0.319476



    # child
    #             singular  plural  total  singular_normalized  plural_normalized
    # AskReddit      26606   29652  56258             0.472928           0.527072
    # askscience     26701   34980  61681             0.432889           0.567111