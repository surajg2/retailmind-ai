# RetailMind AI — Phase 4 Machine Learning Architecture

## 1. Forecasting Objective & Target Definition

- **Core Objective**: Predict daily observed units sold for each product across a **7-day forecasting horizon** ($t+1 \dots t+7$).
- **Target Variable ($y(t)$)**: `observed_units_sold`
- **Observed vs. Censored Demand Distinction**:
  - The model target represents **OBSERVED UNITS SOLD** recorded in daily store sales transactions.
  - Observed sales can be **censored** on days when products experience a stockout (`is_stockout = TRUE` or `stock_available = 0`).
  - RetailMind AI explicitly distinguishes observed sales from unobserved true customer demand. The system does not fabricate latent demand or attempt unverified demand reconstruction at this milestone.

---

## 2. Feature Engineering & Temporal Cutoff Rules

All features are constructed per `(business_id, product_id)` time-series:

### Feature List
1. **Calendar Features**: `day_of_week`, `day_of_month`, `month`, `week_of_year`, `is_weekend`
2. **Lag Features**: `lag_1`, `lag_7`, `lag_14`, `lag_28`
3. **Rolling Window Features**:
   - `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`
   - `rolling_std_7`, `rolling_std_14`, `rolling_std_28`
4. **Business & Exogenous Variables**: `selling_price`, `promotion`, `holiday`, `has_festival`, `stock_available`, `is_stockout_feature`
5. **Product Categoricals**: `category_code`, `product_id_code`

### Temporal Leakage Cutoff Rules
- **Lag Rule**: For target date $t$, `lag_1` uses observation $t-1$, `lag_7` uses observation $t-7$.
- **Rolling Window Rule**: Target series is shifted by 1 day FIRST (`units_sold.shift(1)`), and then rolling statistics are calculated over windows $W \in \{7, 14, 28\}$. This guarantees that target day $t$'s observation is **NEVER** present inside any rolling window.
- **History Drop**: Initial records (first 28 days of history per product) lacking sufficient lag history are dropped. No forward-filling or future-data interpolation is performed.

---

## 3. Stockout & Censoring Treatment

- Observations where `is_stockout == True` or `stock_available == 0` are preserved in the dataset.
- `is_stockout_feature` is provided as an exogenous feature to inform the model of inventory state.
- Stockout percentage is calculated and reported as part of pipeline telemetry:
  $$\text{Stockout Percentage} = \frac{\text{Confirmed Stockout Records}}{\text{Total Historical Records}} \times 100\%$$

---

## 4. Chronological Train / Validation / Test Split

- **Splitting Strategy**: Strict chronological partitioning by date across the business's timeline:
  - **70% TRAIN**: Oldest chronological historical observations.
  - **15% VALIDATION**: Intermediate chronological period.
  - **15% TEST**: Latest chronological period (held-out future observations).
- **No Random Splitting**: `train_test_split` with random shuffling is strictly forbidden to prevent temporal data leakage.
- **Data Isolation**: All dataset extraction and feature generation operations are tenant-scoped by `business_id`. A business never accesses another business's training data.

---

## 5. Baseline Models & XGBoost Formulation

### Baseline 1 — Naive
$$\hat{y}_{naive}(t) = y(t-1) \quad (\text{using } lag\_1)$$

### Baseline 2 — Seasonal Naive
$$\hat{y}_{snaive}(t) = y(t-7) \quad (\text{using } lag\_7)$$

### XGBoost Tabular Regressor
$$y(t) = f(X(t))$$
- Trained on supervised tabular feature matrix $X \in \mathbb{R}^{N \times 23}$ using `XGBRegressor` with conservative hyperparameters (`n_estimators=100`, `max_depth=4`, `learning_rate=0.05`).
- Predictions are clipped at zero ($\hat{y} = \max(0, f(X))$) to ensure physical validity.

---

## 6. Evaluation Framework & Model Acceptance Criteria

### Metrics
- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- **Mean Absolute Percentage Error (MAPE)**: Calculated optionally only over non-zero actual observations ($y_i > 0$) to prevent division-by-zero errors.

### Model Acceptance Rule
XGBoost is evaluated on the held-out **TEST** period against Naive and Seasonal Naive baselines.
- **Rule**: XGBoost is designated as the preferred production model **ONLY** if:
  $$\text{MAE}_{XGBoost} < \min(\text{MAE}_{Naive}, \text{MAE}_{Seasonal\_Naive})$$
- If XGBoost does not outperform the best baseline, the system reports `"XGBoost did not outperform the baseline."` and falls back to the best performing baseline without manipulating metrics or data.

---

## 7. Artifact Storage & Security

- Models are saved locally in `ml/artifacts/xgboost_demand_model.joblib`.
- Metadata JSON (`xgboost_demand_model_metadata.json`) records training timestamps, business scope, feature lists, chronological date ranges, test set metrics, baseline metrics, and stockout statistics.
- **Security Constraint**: No passwords, database connection strings, JWT secrets, or API keys are written to model artifacts.
