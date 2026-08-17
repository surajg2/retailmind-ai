# RetailMind AI — Demand & Operational Intelligence Console

> **Predict observed demand. Monitor model drift. Detect sales anomalies.**

RetailMind AI is a production-ready, full-stack operational intelligence platform tailored for retail businesses (such as general stores and FMCG merchants).

---

## Scope & Architectural Principles

> [!IMPORTANT]
> **Observed Demand vs. Unobserved Customer Demand**:
> RetailMind AI forecasts predict **Observed Units Sold** recorded in store sales transactions.
> Stockout-censored demand has not been reconstructed. Predictions estimate future observed sales patterns.
> 
> **Deferred Scope Statement**:
> **Phase 4D (Inventory Decision Engine) is intentionally deferred.**
> RetailMind AI currently focuses strictly on demand forecasting, forecast evaluation, model performance monitoring, and historical sales anomaly detection. It does not fabricate automated reorder recommendations, safety stock thresholds, or lead-time demand calculations.

---

## Key Features

1. **Multi-Tenant Foundation & Security** (Phase 1)
   - PostgreSQL 18 + SQLAlchemy ORM v2
   - JWT authentication & Bcrypt password hashing
   - Strict business-level tenant isolation across all endpoints and queries

2. **Atomic Sales CSV Ingestion & Stockout Semantics** (Phase 2)
   - Two-phase atomic CSV validator with zero-partial-write guarantee
   - Probabilistic 7,300-record synthetic sales dataset generator
   - Explicit distinction between confirmed stockouts (`is_stockout == True`) and zero EOD inventory (`stock_available == 0`)

3. **Analytics Dashboard & Dynamic Date Presets** (Phase 3)
   - Dynamic relative date filtering anchored to `MAX(sale_date)` in the database
   - Historical sales trend, category revenue share, top products, and data quality indicator

4. **Leakage-Safe XGBoost Demand Forecasting** (Phase 4A / 4B / 4C)
   - Chronological 70/15/15 train/validation/test split
   - Shifted rolling features preventing temporal data leakage
   - Benchmark comparison: Naive, Seasonal Naive, and XGBoost regressor
   - 7-day prediction persistence in PostgreSQL (`predictions` table)
   - Option A forecast replacement strategy (duplicate forecast version cleanup)
   - Recharts visual separation: solid silver historical sales vs purple dashed forecast line

5. **Forecast Evaluation, Model Monitoring & Anomaly Intelligence** (Phase 5)
   - **Forecast Evaluation**: Matches persisted predictions against historical sales actuals. Calculates MAE, RMSE, and Zero-Safe MAPE.
   - **Model Error Drift Monitoring**: Statistical comparison of recent 7-day MAE vs historical baseline MAE to classify drift status (`STABLE`, `WATCH`, `DEGRADED`).
   - **Historical Sales Anomaly Detection**: Deterministic 21-day rolling median & MAD/IQR anomaly detection (`HIGH_SALES`, `LOW_SALES`, `ZERO_SALES`, `PROMOTION_SPIKE`, `PRICE_CHANGE`), treating stockouts separately.

---

## Technical Stack

* **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Recharts, Lucide Icons, Axios, React Router v6
* **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy ORM v2 (`Numeric(10,2)` monetary fields, `Date` aggregations)
* **Database & Migrations**: PostgreSQL 18, Alembic (`001` through `004`)
* **Machine Learning**: XGBoost, scikit-learn, joblib, pandas, NumPy
* **Testing**: Pytest & FastAPI TestClient

---

## Project Structure

```
retailmind-ai/
├── backend/                  # FastAPI backend application & DB models
│   ├── alembic/              # Database migration scripts (001_initial_schema to 004_forecast_persistence)
│   ├── app/                  # Core API routes, DB session, models, schemas, dependencies
│   ├── tests/                # Automated backend tests (test_auth.py, test_sales.py, test_analytics.py, test_forecasts.py, test_phase5_intelligence.py)
│   └── requirements.txt      # Backend Python dependencies
├── ml/                       # Machine Learning forecasting pipeline
│   ├── artifacts/            # Persisted model binaries & metadata JSON
│   ├── services/             # Forecast generation, evaluation, drift monitoring, anomaly detection
│   └── tests/                # ML leakage & baseline test suite
├── frontend/                 # React + TypeScript + Tailwind CSS web app
│   ├── src/                  # App components, pages, context, services, types
│   ├── package.json
│   └── vite.config.ts
├── data/                     # Synthetic data generator & CSV storage
├── docs/                     # Architecture & API documentation
│   ├── architecture.md
│   ├── database.md
│   ├── api.md
│   └── ml_architecture.md
├── .env.example              # Environment variable template
└── .gitignore                # Git exclusions (.env, node_modules, build outputs)
```

---

## Local Setup Instructions

### 1. Environment Configuration
Copy `.env.example` to `.env` and configure your local PostgreSQL database URL:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/retailmind_db
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### 2. Database Migrations
Run Alembic schema migrations:
```powershell
python database/init_db.py
```

### 3. Backend Startup
```powershell
$env:PYTHONPATH="."
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Frontend Startup & Production Build
```powershell
# Development server
cd frontend
npm run dev

# Production build check
npm run build
```

### 5. Running Full Test Suite
```powershell
# Backend test suite (35 test cases)
$env:PYTHONPATH="."
pytest backend/tests -v

# ML test suite (12 test cases)
$env:PYTHONPATH="."
pytest ml/tests -v
```

---

## Known Limitations

- **Observed Demand Limit**: Predictions forecast observed units sold. Demand lost to stockouts is not reconstructed.
- **Minimum Historical Requirement**: Products with fewer than 28 recorded sales dates are skipped during forecast generation.
- **Phase 4D Deferral**: Automated inventory reorder recommendations are intentionally not included.