# RetailMind AI — Demand & Inventory Decision Engine

> **Predict demand. Prevent stockouts. Reduce dead inventory.**

RetailMind AI is a production-grade full-stack demand forecasting and inventory decision engine tailored for small retail businesses such as general and kirana stores.

---

## Technical Stack (Phase 1 & Phase 2 Implemented)

* **Frontend**: React 18, Vite, TypeScript, Tailwind CSS v4, Lucide Icons, Axios, React Router v6
* **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy ORM v2 (`Numeric(10,2)` money types, `Date` daily aggregations)
* **Database**: PostgreSQL 18
* **Database Migrations**: Alembic
* **Authentication**: JWT (JSON Web Tokens), Bcrypt password hashing
* **Data Engine**: 2-Phase Atomic CSV Validator & Ingestion Engine, Probabilistic Synthetic Sales Generator
* **Testing**: Pytest & FastAPI TestClient

---

## Project Structure

```
retailmind-ai/
├── backend/                  # FastAPI backend application & DB models
│   ├── alembic/              # Database migration scripts (001_initial_schema, 002_sales_phase2_schema)
│   ├── app/                  # Application code (API, Core, DB, Models, Schemas, Services)
│   ├── tests/                # Automated backend tests (test_auth.py, test_sales.py)
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React + TypeScript + Tailwind CSS application
│   ├── src/                  # App, Components, Context, Pages, Services
│   ├── package.json
│   └── vite.config.ts
├── database/                 # Database migration runner
│   └── init_db.py
├── data/                     # Data generation & CSV storage
│   ├── generate_synthetic_data.py
│   └── synthetic_sales_data.csv  # 7,300 daily records (20 products x 365 days)
├── ml/                       # Machine Learning forecasting models (Phase 3)
├── docs/                     # Comprehensive documentation
│   ├── architecture.md
│   ├── database.md
│   └── api.md
├── .env.example              # Environment variables template
└── .gitignore                # Git exclusions (.env, node_modules, build outputs)
```

---

## Sales Data & CSV Ingestion (Phase 2)

### CSV Format Specification
```csv
# RETAILMIND AI - SYNTHETIC DATASET
date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-01-01,SKU-GROC-001,Aashirvaad Whole Wheat Atta 5kg,Atta & Flours,39,245.00,0,0,,132
```

- **Comment Headers**: CSV parser strips `#` comment headers automatically.
- **Normalization**: `sku` maps to `Product` lookup/creation. `product_name` and `category` are not duplicated in the `sales` table. Empty festival entries normalize to PostgreSQL `NULL`.
- **Atomic Two-Phase Validation**: If any row contains an error (such as an invalid date, negative quantity, invalid monetary value, intra-file duplicate, database duplicate, or SKU metadata conflict), **zero rows** are inserted.

### Generating Synthetic Data
To generate the 7,300-record probabilistic synthetic sales dataset:
```powershell
python data/generate_synthetic_data.py
```

---

## Local Setup Instructions

### 1. Environment Configuration
Ensure `.env` contains your PostgreSQL connection string:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/retailmind_db
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

### 4. Running Backend Test Suite
```powershell
$env:PYTHONPATH="."
pytest backend/tests -v
```