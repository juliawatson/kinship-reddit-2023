# To run this script, use the terminal command
# RScript sig_test.R

get_subreddit_colname <- function(data_frame) {
  for (curr_col in colnames(data_frame)) {
    if (startsWith(curr_col, "subreddit_")) {
      return(curr_col)
    }
  }
}

write_model_summary <- function(model, subreddit_pair_str, kinship_group, output_dir, kinship_data) {
  sink(sprintf("%s/%s.%s.sig_test.txt", output_dir, subreddit_pair_str, kinship_group))
  print(summary(model))
  print(sprintf("n_observations=%d", nrow(kinship_data)))
  sink()

  write.csv(
    as.data.frame(summary(model)$coef), 
    file=sprintf("%s/%s.%s.sig_test.csv", output_dir, subreddit_pair_str, kinship_group))
}



subreddit_pairs = list(
  c("AskReddit", "askscience"), 
  c("parenting", "entitledparents")
)
kinship_groups = list("parent", "child", "partner", "sibling")
# Define shared predictors
ref_prag_factors <- c("singular", "specific")
for (kin_group in kinship_groups) {
    for (subreddit_pair in subreddit_pairs) {
      # Load data
      subreddit_pair_str <- paste(subreddit_pair, collapse="_")
      data_filename <- sprintf("data/referential_pragmatic_regression/%s.sig_test.csv",
                              subreddit_pair_str)
      kinship_data <- read.csv(data_filename)

      # Filter to only include the kin group
      kinship_data <- kinship_data[kinship_data$kinship_group == kin_group,]
      
      subreddit_contrast <- get_subreddit_colname(kinship_data)

      # Train model
      curr_factors <- c(ref_prag_factors, subreddit_contrast)
      model <- glm(
        as.formula(paste("gendered~", paste(curr_factors, collapse="+"))),
        data=kinship_data,
        family=binomial())

      # Print output
      write_model_summary(model, subreddit_pair_str, kin_group, "results/part_2", kinship_data)

      # Train model
      curr_factors <- c(subreddit_contrast)
      model <- glm(
        as.formula(paste("gendered~", paste(curr_factors, collapse="+"))),
        data=kinship_data,
        family=binomial())

      # Print output
      write_model_summary(model, subreddit_pair_str, kin_group, "results/part_1", kinship_data)
    }
}