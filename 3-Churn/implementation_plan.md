# Telco Churn Analysis — Implementation Plan

## Phase 1: Load Raw Data & Split Immediately
- Load `WA_Fn-UseC_-Telco-Customer-Churn.csv` with no transformations applied
- Drop `customerID` (non-predictive identifier — safe to remove before split)
- Perform a stratified 80/20 split on the raw data:
  - **80% training set** — used exclusively to fit the model
  - **20% test set** — held out entirely; touched only once at the very end to report final metrics
- No separate validation set is needed: random forest uses out-of-bag (OOB) bootstrap samples internally to estimate generalisation error and guide tuning
- Set `seed = 42` for reproducibility
- Print row counts and churn distribution for each split as a sanity check

## Phase 2: Preprocessing (Applied Independently Per Split)
- For each split separately:
  - Coerce `TotalCharges` from character to numeric
  - Drop rows with resulting NAs (~11 rows, expected to fall in training; verify none appear in test)
  - Convert `Churn` to a factor with levels `No` / `Yes`
- No transformation is fit on test data using information from the training set

## Phase 3: Exploratory Analysis (Training Set Only)
All plots are derived from the training set only to avoid any look-ahead bias.

- **Feature 1 — Contract type**: stacked bar chart showing the fraction of customers churned vs. not churned for each contract type (Month-to-month, One year, Two year) → `plot_contract_churn.png`
- **Feature 2 — Tenure**: bin tenure into four groups (0–12, 13–24, 25–48, 49–72 months); same stacked bar format → `plot_tenure_churn.png`

## Phase 4: Model Training & Hyperparameter Tuning
- Train random forest models on the **training set only** using `randomForest::randomForest`
- Tune `mtry` (number of features considered at each split) using **OOB error** on the training set
  - Test a range of mtry values (e.g., 2, 4, 6, 8, `floor(sqrt(p))`)
  - Select the value that minimises OOB error
- Fix `ntree = 500` (OOB error stabilises well before this)
- Train the final model on the **training set** using the selected mtry; test set is not touched at this stage

## Phase 5: Final Evaluation (Test Set — Used Once)
- Generate predictions on the **test set** using the final trained model
- Compute and print:
  - Confusion matrix
  - Accuracy
  - Precision — of predicted churners, how many actually churned
  - Recall — of actual churners, how many did the model catch

## Phase 6: Variable Importance Plot
- Extract feature importances (Mean Decrease Gini) from the final model
- Plot top 10 features as a horizontal bar chart → `plot_feature_importance.png`
