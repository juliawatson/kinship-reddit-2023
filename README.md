# Communicative need and kinship terms

This project includes the code for the paper:

Watson, J., Walker, S., Stevenson, S., & Beekhuizen, B. (2021) Communicative need shapes choices to use gendered vs. gender-neutral kinship terms across online communities. In CogSci.


The data for this project can be found here: https://osf.io/q4gfd/

The sections that follow describe how this data was collected and how it is stored ("Data Collection and Processing"), as well as the scripts used to conduct the analyses for the paper ("Analyses").


## Data Collection and Processing

### Frequency dataset
These are files for collecting the frequency of kinship terms per every ten million words.   
1. `collect_data.py`: This goes through each subreddit and writes the frequency of each
  term per million in its own csv file in the folder `data/part_1_need_probabilities/`.

### Main dataset
These are files used to create the dataset we analyzed. 
1. `scrape_data.py`: This scrapes comments  from a list of subreddits.  
    This file requires the file `terms.csv`, containing the list of kinship terms to search for.  
    Each subreddit's query is written to its own file in the subdirectory `data/kinship_terms_json`.
2. `extract_kinship_terms.py`: This takes the scraped comments and extracts necessary information from them
    (ex. specificity, whether a term is singular) and writes the results to a csv file.  
    For every subreddit ran in `extract_kinship_terms.py`, its corresponding json file must exist (i.e. `scrape_data.py`
    must have been run on the same subreddit). It also requires the file `terms.csv`.
    The results of this file are written to `data/kinship_terms_csv`, with each subreddit getting its own file.  
3. `calculate_p_gendered_feminine.py`: This file uses BERT to calculate the following probabilities:
    * probability of getting a particular kinship term for each kinship term group, given a specific/singular context
    * probability of getting a gendered kinship term given the context
    * probability of getting a feminine kinship term given that it's gendered  

    This file requires the data files `terms.csv`, and the files outputted from running `extract_kinship_terms.py`.   
For each subreddit and kinship term group pairing, it creates two new files: 
    * P(kinship term) is stored in `data/probabilities_specific_singular`
    * P(gendered | context) and P(feminine | context) are stored in `data/p_gendered_feminine`

## Analyses
Files used for calculating results.  

### Part 1
1. `part_1_frequency_chi_squared.py`: Runs chi squared tests for part 1 using the frequency per ten million data.   
    Output of significance tests are printed to console. 
    Requires the `terms.csv` file. Uses `TOTAL_WORD` values and `data/part_1_need_probabilities/` files from running `collect_data.ipynb`.  
2. `parts_1_2_convert_csv_for_sig_testing.py`: Writes csv files in order to run logistic regressions for differences in use of gendered terms.    
    Outputs csv files to `data/referential_pragmatic_regression` for each subreddit pair.  
    Requires the files from running `extract_kinship_terms.py`.    
3. `parts_1_2_sig_test.R`: Runs significance tests for differences in use of gendered terms.  
    Outputs .csv and .txt files in `results/part_1` and `results/part_2`.  
    Requires the csv files from running `parts_1_2_convert_csv_for_sig_testing.py`.   
4. `part_1_barplots.py`: Creates bar plots representing ratios for gender vs. gender-neutral terms for each kinship 
    term group for each subreddit.  
    Outputs the results in `images/part_1_bar`. Also creates aggregate counts for each subreddit, which is used to
    calculate the ratios for the bar graphs, and stored in `data/aggregate_data/`.  
    Requires files from `data/kinship_terms_csv`, which are created from running `extract_kinship_terms.py`.
### Part 2
1. `part_2_chi_squared_ref_prag.py`: Runs chi-squared tests for communicative need differences. 
    Outputs the results of the test to console.  
    Requires files from `data/aggregate_data`, which occur after running `part_1_barplots`.   
2. `parts_1_2_convert_csv_for_sig_testing.py`: see **Part 1**. 
3. `parts_1_2_sig_test.R`: see **Part 1**. 
4. `part_2_barplots.py`: Creates bar plots with grammatical contexts along x-axis.  
    Outputs visualizations to `images/part_2_bar`. 
    Requires the files from running `extract_kinship_terms.py` (stored in `data/kinship_terms_csv`),
    the aggregate data files from running `part_1_barplots` (stored in `data/aggregate_data`), and `terms.csv`. 
### Part 3
1. `part_3_need_tests.py`: Runs tests for differences in communicative need and also creates KDE plots.  
    Outputs results of Mann-Whitney U tests to console. Saves KDE plots to `images/p_gendered_kde_plots`.  
    Requires the files outputted by running `part_2_convert_csv_for_sig_testing.py` (found in `data/p_gendered_feminine_regression`).  
2. `part_3_convert_csv_for_sig_testing.py`: Creates csv files to run significance tests for differences in use of gendered terms.  
    Outputs the csv files to `data/p_gendered_feminine_regression`.   
    Requires `terms.csv`, the files created from running `extract_kinship_terms.py` (stored in `data/kinship_terms_csv`),
    and the files created from running `calculate_p_gendered_feminine.py` (found in `data/p_gendered_feminine`).  
    **NOTE (and should check for other files as well): has an if condition for lgbt-baseline.**  
3. `part_3_sig_test.R`: Runs significance tests for differences in use of gendered terms.  
    Outputs the results of the tests to `results/part_3` and `results/part_3_baseline` as csv and txt files.  
    Requires the files in `data/p_gendered_feminine_regressions` (see above).
