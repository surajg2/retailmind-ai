# RetailMind AI Architecture — Phase 1

RetailMind AI is a production-grade full-stack demand forecasting and inventory decision engine tailored for retail businesses (such as Kirana and general stores).

---

## High-Level System Architecture

```
+-------------------------------------------------------------------+
|                        React Frontend                             |
|    (Vite, TypeScript, Tailwind CSS, React Router, Axios)          |
+-------------------------------------------------------------------+
                                 |
                                 | HTTP / REST (JWT Auth)
                                 v
+-------------------------------------------------------------------+
|                        FastAPI Backend                            |
|  - Auth Router (/auth/register, /auth/login, /auth/me)           |
|  - Health Router (/health - DB ping check)                        |
|  - Core Security (Bcrypt password hashing & JWT generation)      |
|  - Dependency Injection (Session management & Bearer Auth)       |
+-------------------------------------------------------------------+
                                 |
                                 | SQLAlchemy ORM
                                 v
+-------------------------------------------------------------------+
|                     PostgreSQL Database                           |
|  - Businesses, Users, Products, Sales, Inventory                 |
|  - Festivals, Predictions, Recommendations                       |
|  - Schema managed strictly via Alembic migrations                |
+-------------------------------------------------------------------+
```

---

## Directory & Package Layout

```
retailmind-ai/
├── backend/
│   ├── alembic/              # Alembic database migration scripts
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── app/
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── api/              # API Endpoints (Health, Auth, Dependencies)
│   │   ├── core/             # Configuration & Security (JWT, Bcrypt)
│   │   ├── db/               # SQLAlchemy engine & session maker
│   │   ├── models/           # SQLAlchemy ORM models
│   │   └── schemas/          # Pydantic validation schemas
│   ├── tests/                # Pytest automated test suite
│   ├── alembic.ini           # Migration settings
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Vite + React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/       # Reusable components & ProtectedRoute
│   │   ├── context/          # AuthContext provider
│   │   ├── pages/            # Login, Register, Dashboard pages
│   │   ├── services/         # Axios API interceptor client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css         # Tailwind & custom glassmorphism CSS
│   ├── package.json
│   └── vite.config.ts
├── database/                 # Database initialization scripts
│   └── init_db.py
├── data/                     # Sample datasets (Phase 2)
├── ml/                       # Machine learning models (Phase 2)
├── docs/                     # Technical documentation
│   ├── architecture.md
│   ├── database.md
│   └── api.md
├── .env.example
├── .gitignore
└── README.md
```

---

## Core Technical Decoupling

1. **Schema Migration Isolation**: Schema modifications are performed strictly via Alembic migrations. FastAPI startup never auto-creates tables via `Base.metadata.create_all()`.
2. **Stateless JWT Authentication**: Bearer JWT tokens contain the user ID subject and expiration timestamp. Endpoints validate incoming tokens per request.
3. **Environment Security**: Sensitive keys and database connection strings are loaded exclusively from `.env`.
