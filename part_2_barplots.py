import os
import pandas as pd  # library for structured dataFrames (like tables or Excel sheets)
from matplotlib.colors import ListedColormap
from part_1_barplots import create_groups, plot_clustered_stacked

OUTPUT_DIR = f"images/part_2_bar"

GENDERED = "#1E18A3"
GENDER_NEUTRAL = "#7670FF"
FEMININE = "#FF6522"
GREEN = "#65CC4F"
DARK_GREEN = "#2F6623"

COLORMAP = ListedColormap([GENDERED, GENDER_NEUTRAL])


def get_dataframes_for_plotting(file: str, group: dict):
    """
    Turn aggregated data into pandas dataframes to graph.
    """
    dataframe = pd.read_csv(file)
    d = {}
    start = 0
    for gr in group:  # get data for each kinship group
        dataframe['group'] = dataframe.apply(lambda row: row['group'].lower(), axis=1)
        g = dataframe[dataframe['group'] == gr]
        g = g.dropna()   # removed total bars
        g, start = set_df_index(g, '[sg, specific]', start)
        d[gr] = normalize_df(g)

    return d


def set_df_index(df, index_name: str, start: int):
    """Set index of dataframe based on size of dataframe.

    Because df is a slice of a larger dataframe, start is the index at which the rows in df start.
    """
    lst = []
    for i in range(len(df)):
        if df['specific'].iloc[i] == 'specific':
            val = 'spec'
        else:  # N/A shows up as nan
            val = df['specific'].iloc[i][:3]  # take the first 3 chars

        if df['singular'].iloc[i] is True:
            val = '+sg ' + val
        elif df['singular'].iloc[i] is False:
            val = '-sg ' + val
        lst.append(val)
    df[index_name] = lst
    df = df.set_index(index_name)
    return df, start + len(df)


def normalize_df(df):
    """Return dataframe with normalized columns 'gendered' and 'gender-neutral'.

    Also, if df['gendered'] + df['gender-neutral'] for any row adds to 0, then the corresponding cells for
    gendered % and gender-neutral % will be nan.
    """
    df['gendered %'] = df['gendered'] / (df['gendered'] + df['gender-neutral'])
    df['gender-neutral %'] = df['gender-neutral'] / (df['gendered'] + df['gender-neutral'])
    return df[['gendered %', 'gender-neutral %']]


def run_functions(group, subreddits):
    dfs = {}
    for subreddit_pair in subreddits:
        for subreddit in subreddit_pair:
            # this will write an aggregated csv for each subreddit
            filename = f'data/aggregated_data/{subreddit}.comment.kinship_terms.aggregated_data.csv'
            dfs[subreddit] = get_dataframes_for_plotting(filename, group)
        for gr in group:
            # create pngs for each kinship term group
            t = ' & '.join(subreddit_pair)
            path_name = '_'.join(subreddit_pair)
            lst = [dfs[subreddit][gr] for subreddit in subreddit_pair]
            if not os.path.exists(f'{OUTPUT_DIR}/{path_name}'):  # make subdirectory if it does not already exist
                os.makedirs(f'{OUTPUT_DIR}/{path_name}')
            plot_clustered_stacked(data_frames=lst, labels=subreddit_pair, title=f'{t}: {gr} terms',
                                   output_path=f'{OUTPUT_DIR}/{path_name}/part2_barplots_{path_name}_{gr}.png')
            print(f'{gr} has been converted to an image!')


if __name__ == "__main__":
    group, gender_neutral, _ = create_groups('terms.csv')
    subreddits = [("AskReddit", "askscience"), ("Parenting", "entitledparents")]

    run_functions(group, subreddits)
