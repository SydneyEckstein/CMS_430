# Telco Customer Churn Analysis — Writeup

## Exploratory Analysis

Two features were examined for their relationship to churn. Customers on **month-to-month contracts** churned at dramatically higher rates than those on one- or two-year contracts, suggesting that longer commitments act as a natural retention mechanism. **Tenure** showed a similarly strong pattern — churn was highest in the first 12 months and declined steadily as customer tenure increased, indicating the early relationship is the highest-risk window.

## Model

A random forest (500 trees) was trained on 80% of the data, with 20% held out for final evaluation. The `mtry` hyperparameter was tuned using out-of-bag (OOB) error on the training set, eliminating the need for a separate validation set.

## Results

|                | Predicted No | Predicted Yes |
|----------------|-------------|--------------|
| **Actual No**  | 940         | 91           |
| **Actual Yes** | 193         | 180          |

- **Accuracy: 79.8%**
- **Precision: 66.4%**
- **Recall: 48.3%**

Recall is the weakest metric — the model misses roughly half of actual churners due to class imbalance (~27% churn rate), which biases predictions toward "No."

## Recommended Course of Action

Use the model to proactively flag at-risk customers — particularly those on month-to-month contracts in their first year — and offer targeted retention incentives. Lowering the classification threshold below 0.5 would improve recall, which is the more valuable trade-off since a missed churner costs more than an unnecessary retention offer. Longer-term, incentivizing new customers to commit to annual contracts early directly addresses the two strongest predictors of churn.
