import csv
import os
import pandas as pd  # library for structured dataFrames (like tables or Excel sheets)
import matplotlib.pyplot as plt  # library for plotting
import collections  # library for the dictionary to keep track of kinship term counts
from matplotlib.colors import ListedColormap
import numpy as np


OUTPUT_DIR = f"images/part_1_bar"

GENDERED = "#1E18A3"
GENDER_NEUTRAL = "#7670FF"
FEMININE = "#FF6522"
GREEN = "#65CC4F"
DARK_GREEN = "#2F6623"

COLORMAP = ListedColormap([GENDERED, GENDER_NEUTRAL])


def get_dataframes_for_plotting(file: str, group: dict, gender_neutral: set, kinship_groups):
    """
    Turn aggregated data into pandas dataframes to graph.
    """
    input_file = aggregate_counts(file, group, gender_neutral)
    dataframe = pd.read_csv(input_file, index_col="group")
    dataframe = dataframe[[item not in ["specific", "generic", "other"] 
                           for item in dataframe["specific"]]]  # these are the "total" rows
    dataframe = dataframe.loc[[item.lower() for item in kinship_groups]]
    return normalize_df(dataframe)


def normalize_df(df):
    """Return dataframe with normalized columns 'gendered' and 'gender-neutral'.

    Also, if df['gendered'] + df['gender-neutral'] for any row adds to 0, then the corresponding cells for
    gendered % and gender-neutral % will be nan.
    """
    df['gendered %'] = df['gendered'] / (df['gendered'] + df['gender-neutral'])
    df['gender-neutral %'] = df['gender-neutral'] / (df['gendered'] + df['gender-neutral'])
    return df[['gendered %', 'gender-neutral %']]


def aggregate_counts(file: str, group: dict, gender_neutral: set):
    """Count values in provided csv file and write to new csv file."""
    dict_of_terms = collections.defaultdict(int)
    # Create dictionary mapping a tuple [(kinship term, +/- gendered, specific/other, +/- singular)] to a number
    # So the phrase 'all my sisters' were in file as a comment body, it would correspond
    # to the key ('sibling', 'true', 'specific', 'false'). Values are kept in lower case for discrepancy across
    # .csv file editors in case of editing (ex. Excel changes 'True' to 'TRUE').

    output = file[:file.index('.csv')] + '.aggregated_data.csv'
    if '/kinship_terms_csv' in output:   # this is not a test file
        output = output.replace('kinship_terms_csv', 'aggregated_data')

    # count data
    with open(file, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for key in group:
                if row['kinship_term'] in group[key]:
                    gr = key
                    break
            specific = "specific" if row["specific"].lower() == "specific" else "other"
            dict_of_terms[(gr, str(row['kinship_term'] not in gender_neutral).lower(), specific,
                           row['singular'].lower())] += 1
            # add one for the total count as well
            dict_of_terms[(gr, str(row['kinship_term'] not in gender_neutral).lower(), 'n/a', 'n/a')] += 1

    # output to new csv file
    with open(output, 'w', encoding="utf-8", newline='') as csv_writer:
        writer = csv.DictWriter(csv_writer, delimiter=',',
                                fieldnames=['group', 'specific', 'singular', 'gendered', 'gender-neutral'])
        writer.writeheader()
        for gr in group:  # write 5 rows per group
            temp = {'group': gr}
            for curr_specific, curr_singular in [('N/A', 'N/A'), ('specific', True),
                                                 ('other', True),
                                                 ('specific', False),
                                                 ('other', False)]:
                temp['specific'], temp['singular'] = curr_specific.lower(), str(curr_singular).lower()
                temp['gendered'] = dict_of_terms[(gr, 'true', curr_specific.lower(), str(curr_singular).lower())]
                temp['gender-neutral'] = dict_of_terms[(gr, 'false', curr_specific.lower(),
                                                        str(curr_singular).lower())]
                writer.writerow(temp)
                # write gendered and gender-neutral versions of the corresponding specific and singular values
    return output


def create_groups(terms_file: str):
    """Create and return the following variables from terms_file (should be a csv):
        - group, a dictionary mapping a kinship term group (string) to a set of its kinship term lemmas
        - gender_neutral, a set containing all lemmas of gender-neutral kinship terms.
        - masculine, a set containing all lemmas of masculine kinship terms
    """
    group = {}
    gender_neutral = set()
    masculine = set()
    with open(terms_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            # rows should be organized as term,lemma,group,gender-neutral (bool),masculine (bool)
            if row['group'] not in group:
                group[row['group']] = set()
            group[row['group']].add(row['lemma'])  # keep only lemmas in each group

            if str(row['gender_neutral']) == 'True':
                gender_neutral.add(row['lemma'])  # keep only lemmas of gender-neutral terms

            if str(row['masculine']) == 'True':
                masculine.add(row['lemma'])  # keep only lemmas of masculine terms

    return group, gender_neutral, masculine


def run_functions(group, gender_neutral, subreddit_pair, kinship_groups, axe=None):
    dfs = {}
    for subreddit in subreddit_pair:
        # this will write an aggregated csv for each subreddit
        filename = f'data/kinship_terms_csv/{subreddit}.comment.kinship_terms.csv'
        dfs[subreddit] = get_dataframes_for_plotting(filename, group, gender_neutral, kinship_groups)

    # create pngs for each kinship term group
    t = ' & '.join(subreddit_pair)
    path_name = '_'.join(subreddit_pair)
    lst = [dfs[subreddit] for subreddit in subreddit_pair]
    plot_clustered_stacked(data_frames=lst, labels=subreddit_pair, title=f'{t}',
                           output_path=f'{OUTPUT_DIR}/{path_name}.png', axe=axe, legend=False)
    print(f'{subreddit_pair} has been converted to an image!')


def plot_clustered_stacked(
        data_frames, labels, title, output_path, H="//", colormap=COLORMAP, axe=None,
        legend=True, **kwargs):
    """Create a clustered stacked bar plot.

    data_frames is a list of pandas dataframes. The dataframes should have
        identical columns and index
    labels is a list of the names of the dataframe, used for the legend
    title is a string for the title of the plot
    H is the hatch used for identification of the different dataframe

    Copy-pasted from stacked_group_bargraph.py
    """
    n_df = len(data_frames)
    n_col = len(data_frames[0].columns)
    n_ind = len(data_frames[0].index)

    save_figure = False
    if axe is None:
        if n_ind > 2:
            figsize=[6.4, 4]
        else:
            figsize=[3.2, 4]

        plt.figure(figsize=figsize)
        axe = plt.subplot(111)
        save_figure = True

    for df in data_frames:  # for each data frame
        axe = df.plot(kind="bar",
                      linewidth=0,
                      stacked=True,
                      ax=axe,
                      legend=False,
                      grid=False,
                      colormap=colormap,
                      **kwargs)  # make bar plots

    h, l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    xtick_offset = 1 / float(n_df + 1) / 2
    xticks = (np.arange(0, 2 * n_ind, 2) + xtick_offset) / 2.

    subreddit_ticks = []
    for item in xticks:
        subreddit_ticks += [item - xtick_offset, item + xtick_offset]
    xticks = sorted(list(xticks) + subreddit_ticks)

    index_items = list(df.index)
    xtick_labels = []
    for item in index_items:
        if "parenting & entitledparents" in title.lower():
            xtick_labels += ["P", "\n" + item, "E"]
        else:
            xtick_labels += ["AR", "\n" + item, "AS"]

    axe.set_xticks(xticks)
    axe.set_xticklabels(xtick_labels, rotation=0)
    axe.tick_params(axis=u'both', which=u'both',length=0)

    axe.set_xlabel("")

    title = title.replace("askscience", "AskScience")
    title = title.replace("parenting", "Parenting")
    title = title.replace("entitledparents", "EntitledParents")

    axe.set_title(title)
    axe.set_xlim(xticks[0] - xtick_offset * 4, xticks[-1] + xtick_offset * 4)

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="gray", hatch=H * i))

    if legend:
        legend_labels = ["gendered", "gender neutral"]
        handles, _ = axe.get_legend_handles_labels()
        handles = handles[:2]
        l1 = axe.legend(handles, legend_labels, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.2))
        plt.subplots_adjust(top=0.85)

    if save_figure:
        plt.savefig(output_path, bbox_extra_artists=(l1,),
                    bbox_inches='tight',
                    dpi=700)


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists('data/aggregated_data'):
        os.mkdir('data/aggregated_data')

    group, gender_neutral, _ = create_groups('terms.csv')
    kinship_groups = ["child", "parent", "partner", "sibling"]

    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [12, 7]}, figsize=[7.4, 4])

    run_functions(group, gender_neutral, ("AskReddit", "askscience"), kinship_groups, axe=ax1)
    run_functions(group, gender_neutral, ("Parenting", "entitledparents"), ["child", "parent"], axe=ax2)

    handles, labels = ax2.get_legend_handles_labels()
    handles = handles[:2]
    labels = ["gendered", "gender neutral"]
    fig.legend(handles, labels, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.0))

    plt.subplots_adjust(top=0.85)

    plt.savefig(f'{OUTPUT_DIR}/part1_barplots.png', dpi=700)
