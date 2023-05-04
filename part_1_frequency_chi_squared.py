import pandas as pd
from scipy.stats import chi2_contingency


kin_terms_data = pd.read_csv("terms.csv")
ONE_MILLION = 1000000


# Copied from output in collect_data.py
TOTAL_WORDS = {
    "askscience": 10000086,
    "askreddit": 10000015,
    "parenting": 10000076,
    "entitledparents": 10000051
}

OUTPUT_CONTINGENCY_TABLE_SUMMARY = False


def get_n_kinship_terms(subreddit_path, kinship_groups):
    data = pd.read_csv(subreddit_path, index_col=0)
    data = data.merge(kin_terms_data, on="term")
    data = data[data["group"].isin(kinship_groups)]
    return data["frequency"].sum()


def run_test(subreddit1, subreddit2, kinship_groups):
    n_kinship_subreddit1 = get_n_kinship_terms(f"data/part_1_need_probabilities/{subreddit1}_frequencies.csv",
                                               kinship_groups=kinship_groups)
    n_kinship_subreddit2 = get_n_kinship_terms(f"data/part_1_need_probabilities/{subreddit2}_frequencies.csv",
                                               kinship_groups=kinship_groups)
    contingency_table = [
        [n_kinship_subreddit1, TOTAL_WORDS[subreddit1] - n_kinship_subreddit1],
        [n_kinship_subreddit2, TOTAL_WORDS[subreddit2] - n_kinship_subreddit2]
    ]

    if OUTPUT_CONTINGENCY_TABLE_SUMMARY:
        print(kinship_groups)
        df = pd.DataFrame(contingency_table, columns=["kinship term", "other word"], index=[subreddit1, subreddit2])
        print(df)
        print("")

    else:
        print(f"{subreddit1} vs. {subreddit2} for kinship_groups={kinship_groups}\n")

        statistic, p_value, degrees_freedom, expected_counts = chi2_contingency(contingency_table)
        print(f"\tstatistic={statistic}; p={p_value:.8f}\n")

        kinship_subreddit1_pmw = (n_kinship_subreddit1 / TOTAL_WORDS[subreddit1]) * ONE_MILLION
        kinship_subreddit2_pmw = (n_kinship_subreddit2 / TOTAL_WORDS[subreddit2]) * ONE_MILLION
        print(f"\t{subreddit1}: {n_kinship_subreddit1} kinship terms of {TOTAL_WORDS[subreddit1]} total ({kinship_subreddit1_pmw:.2f} per million words)")
        print(f"\t{subreddit2}: {n_kinship_subreddit2} kinship terms of {TOTAL_WORDS[subreddit2]} total ({kinship_subreddit2_pmw:.2f} per million words)\n")



### Tests for AskReddit vs. AskScience ###
run_test("askreddit", "askscience", kinship_groups=["child"])
run_test("askreddit", "askscience", kinship_groups=["parent"])
run_test("askreddit", "askscience", kinship_groups=["partner"])
run_test("askreddit", "askscience", kinship_groups=["sibling"])

### Test for parenting vs entitledparents ###
run_test("parenting", "entitledparents", kinship_groups=["child"])
run_test("parenting", "entitledparents", kinship_groups=["parent"])


# askreddit vs. askscience for kinship_groups=['child']

# 	statistic=5986.191158480933; p=0.00000000

# 	askreddit: 15245 kinship terms of 10000015 total (1524.50 per million words)
# 	askscience: 4404 kinship terms of 10000086 total (440.40 per million words)

# askreddit vs. askscience for kinship_groups=['parent']

# 	statistic=5707.957193812312; p=0.00000000

# 	askreddit: 12522 kinship terms of 10000015 total (1252.20 per million words)
# 	askscience: 3086 kinship terms of 10000086 total (308.60 per million words)

# askreddit vs. askscience for kinship_groups=['partner']

# 	statistic=6604.458009513613; p=0.00000000

# 	askreddit: 8544 kinship terms of 10000015 total (854.40 per million words)
# 	askscience: 722 kinship terms of 10000086 total (72.20 per million words)

# askreddit vs. askscience for kinship_groups=['sibling']

# 	statistic=2303.0194636843667; p=0.00000000

# 	askreddit: 3562 kinship terms of 10000015 total (356.20 per million words)
# 	askscience: 502 kinship terms of 10000086 total (50.20 per million words)

# parenting vs. entitledparents for kinship_groups=['child']

# 	statistic=17332.154843477434; p=0.00000000

# 	parenting: 107147 kinship terms of 10000076 total (10714.62 per million words)
# 	entitledparents: 54439 kinship terms of 10000051 total (5443.87 per million words)

# parenting vs. entitledparents for kinship_groups=['parent']

# 	statistic=8869.447899141438; p=0.00000000

# 	parenting: 45629 kinship terms of 10000076 total (4562.87 per million words)
# 	entitledparents: 78739 kinship terms of 10000051 total (7873.86 per million words)