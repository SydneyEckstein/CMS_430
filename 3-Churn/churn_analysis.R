library(tidyverse)
library(caret)

# ── Phase 1: Load raw data & split ───────────────────────────────────────────

# Load with no transformations applied
raw_df <- read.csv("WA_Fn-UseC_-Telco-Customer-Churn.csv", stringsAsFactors = TRUE)

# Drop customerID — non-predictive identifier, safe to remove before split
raw_df <- raw_df %>% select(-customerID)

# Stratified 80/20 split on raw data before any preprocessing
set.seed(42)
train_idx <- createDataPartition(raw_df$Churn, p = 0.80, list = FALSE)
train_raw <- raw_df[ train_idx, ]
test_raw  <- raw_df[-train_idx, ]

# Sanity check — row counts and churn distribution per split
cat("── Split summary ──────────────────────────────\n")
cat(sprintf("Training rows : %d\n", nrow(train_raw)))
cat(sprintf("Test rows     : %d\n", nrow(test_raw)))
cat("\nTraining churn distribution:\n")
print(prop.table(table(train_raw$Churn)))
cat("\nTest churn distribution:\n")
print(prop.table(table(test_raw$Churn)))

# ── Phase 2: Preprocessing (applied independently per split) ─────────────────

preprocess_split <- function(df, split_name) {
  # Coerce TotalCharges to numeric (blank strings become NA for tenure=0 customers)
  df$TotalCharges <- as.numeric(as.character(df$TotalCharges))

  # Drop rows with NA — expected only in training set
  n_before <- nrow(df)
  df <- df[!is.na(df$TotalCharges), ]
  n_dropped <- n_before - nrow(df)
  cat(sprintf("%s: dropped %d NA row(s) from TotalCharges\n", split_name, n_dropped))

  # Ensure Churn is a factor with consistent levels
  df$Churn <- factor(df$Churn, levels = c("No", "Yes"))

  df
}

train_df <- preprocess_split(train_raw, "Training")
test_df  <- preprocess_split(test_raw,  "Test")

cat(sprintf("\nFinal training rows : %d\n", nrow(train_df)))
cat(sprintf("Final test rows     : %d\n", nrow(test_df)))

# ── Phase 3: Exploratory analysis (training set only) ────────────────────────

# Feature 1: Contract type
contract_summary <- train_df %>%
  group_by(Contract, Churn) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(Contract) %>%
  mutate(pct = n / sum(n))

p1 <- ggplot(contract_summary, aes(x = Contract, y = pct, fill = Churn)) +
  geom_col(position = "fill") +
  scale_y_continuous(labels = scales::percent) +
  scale_fill_manual(values = c("No" = "#4CAF50", "Yes" = "#F44336")) +
  labs(
    title = "Churn Rate by Contract Type",
    x     = "Contract Type",
    y     = "Proportion of Customers",
    fill  = "Churned"
  ) +
  theme_minimal()

print(p1)
ggsave("plot_contract_churn.png", p1, width = 7, height = 5)
cat("Saved plot_contract_churn.png\n")

# Feature 2: Tenure (binned into groups)
train_df <- train_df %>%
  mutate(tenure_group = cut(tenure,
    breaks = c(0, 12, 24, 48, 72),
    labels = c("0-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"),
    include.lowest = TRUE
  ))

tenure_summary <- train_df %>%
  group_by(tenure_group, Churn) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(tenure_group) %>%
  mutate(pct = n / sum(n))

p2 <- ggplot(tenure_summary, aes(x = tenure_group, y = pct, fill = Churn)) +
  geom_col(position = "fill") +
  scale_y_continuous(labels = scales::percent) +
  scale_fill_manual(values = c("No" = "#4CAF50", "Yes" = "#F44336")) +
  labs(
    title = "Churn Rate by Customer Tenure",
    x     = "Tenure Group",
    y     = "Proportion of Customers",
    fill  = "Churned"
  ) +
  theme_minimal()

print(p2)
ggsave("plot_tenure_churn.png", p2, width = 7, height = 5)
cat("Saved plot_tenure_churn.png\n")

# Drop tenure_group before modelling — derived column, not in test set
train_df <- train_df %>% select(-tenure_group)

# ── Phase 4: Model training & hyperparameter tuning (training set only) ───────

library(randomForest)

# Tune mtry by comparing OOB error across candidate values
# Test set is not touched at any point during this phase
p <- ncol(train_df) - 1  # number of predictors
mtry_candidates <- c(2, 4, 6, 8, floor(sqrt(p)))

cat("\nTuning mtry via OOB error:\n")
oob_errors <- sapply(mtry_candidates, function(m) {
  set.seed(42)
  rf_tune <- randomForest(Churn ~ ., data = train_df, ntree = 500, mtry = m)
  err <- rf_tune$err.rate[500, "OOB"]
  cat(sprintf("  mtry = %2d  |  OOB error = %.4f\n", m, err))
  err
})

best_mtry <- mtry_candidates[which.min(oob_errors)]
cat(sprintf("\nBest mtry: %d (OOB error = %.4f)\n", best_mtry, min(oob_errors)))

# Train final model with best mtry on the full training set
set.seed(42)
rf_model <- randomForest(
  Churn ~ .,
  data       = train_df,
  ntree      = 500,
  mtry       = best_mtry,
  importance = TRUE
)

cat("\nFinal model summary:\n")
print(rf_model)

# ── Phase 5: Final evaluation on test set (used once) ────────────────────────

preds <- predict(rf_model, newdata = test_df)
cm    <- confusionMatrix(preds, test_df$Churn, positive = "Yes")

cat("\n── Confusion Matrix ──────────────────────────\n")
print(cm$table)

accuracy  <- cm$overall["Accuracy"]
precision <- cm$byClass["Precision"]
recall    <- cm$byClass["Recall"]

cat(sprintf("\nAccuracy  : %.4f\n", accuracy))
cat(sprintf("Precision : %.4f  (of predicted churners, how many actually churned)\n", precision))
cat(sprintf("Recall    : %.4f  (of actual churners, how many did the model catch)\n", recall))

# ── Phase 6: Variable importance plot ────────────────────────────────────────

imp_df <- as.data.frame(importance(rf_model)) %>%
  rownames_to_column("Feature") %>%
  arrange(desc(MeanDecreaseGini))

p3 <- ggplot(imp_df[1:10, ], aes(x = reorder(Feature, MeanDecreaseGini), y = MeanDecreaseGini)) +
  geom_col(fill = "#2196F3") +
  coord_flip() +
  labs(
    title = "Top 10 Features by Importance (Mean Decrease Gini)",
    x     = "Feature",
    y     = "Mean Decrease in Gini Impurity"
  ) +
  theme_minimal()

print(p3)
ggsave("plot_feature_importance.png", p3, width = 8, height = 5)
cat("Saved plot_feature_importance.png\n")
