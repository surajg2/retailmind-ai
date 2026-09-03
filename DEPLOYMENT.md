# RetailMind AI — Vercel & Railway Deployment Guide

This guide provides step-by-step instructions for deploying RetailMind AI using:
- **Vercel** for the React Frontend
- **Railway** for the FastAPI & XGBoost Backend
- **Supabase** for PostgreSQL Database

---

## 🏗️ Architecture Stack

| Layer | Platform | Tech Stack |
| :--- | :--- | :--- |
| **Frontend** | **Vercel** | React 18, Vite, TypeScript, Tailwind CSS |
| **Backend** | **Railway** | FastAPI, SQLAlchemy v2, XGBoost, pandas, scikit-learn |
| **Database** | **Supabase** | PostgreSQL 18 |

---

## 🛠️ Step 1: Deploy Backend to Railway

1. Log into your [Railway Dashboard](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select the `retailmind-ai` repository.
4. Railway will automatically detect `railway.json` and `Procfile`.
5. Under **Variables** in your Railway service, add:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
   JWT_SECRET_KEY=super_secret_retailmind_jwt_key_2026_phase1
   ENVIRONMENT=production
   CORS_ORIGINS=https://your-frontend.vercel.app
   PYTHONPATH=.
   ```
6. Under **Settings** -> **Networking**, click **Generate Domain** (e.g., `retailmind-backend.up.railway.app`).
7. Test the health endpoint: `https://retailmind-backend.up.railway.app/health`.

---

## ⚡ Step 2: Deploy Frontend to Vercel

1. Log into your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** -> **Project**.
3. Import your `retailmind-ai` GitHub repository.
4. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `./` (or `frontend`)
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
5. Add **Environment Variable**:
   - `VITE_API_BASE_URL`: `https://retailmind-backend.up.railway.app` (your Railway domain)
6. Click **Deploy**. Vercel will build the frontend and assign a live URL (e.g. `https://retailmind-ai.vercel.app`).

---

## 🗄️ Step 3: Initialize Database Schema

If pointing to a new database instance on Supabase:

```powershell
# Set your production DATABASE_URL
$env:DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
$env:PYTHONPATH="."

# Run Alembic DB migrations
python database/init_db.py
```

---

## ⚙️ Config Files Created in Repository

- [`vercel.json`](file:///c:/Users/Deepak/Desktop/Suraj's%20work/retailmind-ai/vercel.json) — Vercel SPA route rewrite & build settings.
- [`railway.json`](file:///c:/Users/Deepak/Desktop/Suraj's%20work/retailmind-ai/railway.json) — Railway build & healthcheck specification.
- [`Procfile`](file:///c:/Users/Deepak/Desktop/Suraj's%20work/retailmind-ai/Procfile) — Startup command (`uvicorn backend.app.main:app`).
