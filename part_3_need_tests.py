# This script tests for differences in p_gendered between pairs of subreddits.
# This will go in the part 3 section on establishing need differences.

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
import seaborn as sns
import matplotlib.pyplot as plt
import os

COLORS = ["#5632a8", "#3ea832"]


DATA_FORMAT_STR = "data/p_gendered_feminine_regression/{}.sig_test.csv"
IMAGE_FORMAT_STR = "images/p_gendered_kde_plots/part3_kdeplot_{}.{}.kdeplot.png"


def format_subreddit_name(name):
    if name.lower() == "parenting":
        return "Parenting"
    if name.lower() == "entitledparents":
        return "EntitledParents"
    if name.lower() == "askreddit":
        return "AskReddit"
    if name.lower() == "askscience":
        return "AskScience"
    return name


if __name__ == "__main__":
    subreddit_pairs = [("AskReddit", "askscience"), ("parenting", "entitledparents")]
    kinship_groups = ["child", "parent", "partner", "sibling"]
    feature = "p_gendered"

    if not os.path.exists("images/p_gendered_kde_plots/"):
        os.makedirs("images/p_gendered_kde_plots/")

    for subreddit_pair in subreddit_pairs:
        subreddit_str = "_".join(subreddit_pair)
        data_path = DATA_FORMAT_STR.format(subreddit_str)
        for kinship_group in kinship_groups:
            data = pd.read_csv(data_path)
            data = data[data["kinship_group"] == kinship_group]

            subreddit1_data = data[data["subreddit"] == subreddit_pair[0].lower()][feature]
            subreddit2_data = data[data["subreddit"] == subreddit_pair[1].lower()][feature]

            mean_s1 = np.mean(subreddit1_data)
            mean_s2 = np.mean(subreddit2_data)
            n_s1 = len(subreddit1_data)
            n_s2 = len(subreddit2_data)

            statistic, p_value = mannwhitneyu(subreddit1_data, subreddit2_data)

            print(f"{subreddit_pair[0]} vs. {subreddit_pair[1]}: kinship_group={kinship_group}")
            print(f"\tmean {feature} is {mean_s1:.4f} on {subreddit_pair[0]} (n={n_s1}) and {mean_s2:.4f} on "
                  f"{subreddit_pair[1]} (n={n_s2})")
            print(f"\tmann-whitney u statistic={statistic}; p_value={p_value}")
            print("")

            kdeplot_dict = {
                feature: list(subreddit1_data) + list(subreddit2_data),
                "subreddit": [subreddit_pair[0]] * len(subreddit1_data) + [subreddit_pair[1]] * len(subreddit2_data) 
            }
            kdeplot_df = pd.DataFrame(kdeplot_dict)
            kdeplot_df["subreddit"] = [format_subreddit_name(item) for item in kdeplot_df["subreddit"]]
            plt.figure(figsize=[3, 4])
            
            p = sns.kdeplot(data=kdeplot_df, x=feature, hue="subreddit", common_norm=False, palette=COLORS)
            
            lss = ['-', '--']
            handles = p.legend_.legendHandles[::-1]
            for line, ls, handle in zip(p.lines, lss, handles):
                line.set_linestyle(ls)
                handle.set_ls(ls)

            plt.axvline(mean_s1, color=COLORS[0], linestyle="--")
            plt.axvline(mean_s2, color=COLORS[1], linestyle="-")
            plt.xlim(0.5, 1)
            plt.xticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
            plt.xlabel("p(gendered)")
            plt.tight_layout()
            plt.savefig(IMAGE_FORMAT_STR.format("_".join(subreddit_pair), kinship_group), dpi=700)


# AskReddit vs. askscience: kinship_group=child
# 	mean p_gendered is 0.7704 on AskReddit (n=2825) and 0.8054 on askscience (n=2013)
# 	mann-whitney u statistic=2460573.0; p_value=1.310790727038914e-15

# AskReddit vs. askscience: kinship_group=parent
# 	mean p_gendered is 0.9979 on AskReddit (n=19144) and 0.9846 on askscience (n=5121)
# 	mann-whitney u statistic=52402302.0; p_value=2.950892749330287e-14

# AskReddit vs. askscience: kinship_group=partner
# 	mean p_gendered is 0.9304 on AskReddit (n=11391) and 0.9052 on askscience (n=3241)
# 	mann-whitney u statistic=20583279.0; p_value=1.359261400136302e-23

# AskReddit vs. askscience: kinship_group=sibling
# 	mean p_gendered is 0.9986 on AskReddit (n=5511) and 0.9926 on askscience (n=1517)
# 	mann-whitney u statistic=5146758.0; p_value=2.1059478700246453e-43

# parenting vs. entitledparents: kinship_group=child
# 	mean p_gendered is 0.7813 on parenting (n=20391) and 0.7531 on entitledparents (n=4167)
# 	mann-whitney u statistic=44581167.0; p_value=4.968918833557235e-07

# parenting vs. entitledparents: kinship_group=parent
# 	mean p_gendered is 0.9948 on parenting (n=8529) and 0.9963 on entitledparents (n=16373)
# 	mann-whitney u statistic=64727792.0; p_value=2.957885111144488e-21

# parenting vs. entitledparents: kinship_group=partner
# 	mean p_gendered is 0.9437 on parenting (n=11419) and 0.9473 on entitledparents (n=3418)
# 	mann-whitney u statistic=20430898.0; p_value=3.0614281094350164e-05

# parenting vs. entitledparents: kinship_group=sibling
# 	mean p_gendered is 0.9964 on parenting (n=2074) and 0.9976 on entitledparents (n=4138)
# 	mann-whitney u statistic=3830555.0; p_value=4.879510380579334e-12