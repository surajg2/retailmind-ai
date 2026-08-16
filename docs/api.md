# REST API Specification — RetailMind AI (Phase 1, Phase 2 & Phase 3)

Base URL: `http://localhost:8000`  
API Version Prefix: `/api/v1`

---

## 1. Health Monitoring

### `GET /health`
Verifies backend server status and PostgreSQL database connectivity.

---

## 2. Authentication Flow

### `POST /api/v1/auth/register`
Registers a new user and associated store business entity.

### `POST /api/v1/auth/login`
Authenticates email and password, returning a JWT access token.

### `GET /api/v1/auth/me`
Protected endpoint retrieving profile of authenticated user. Requires `Authorization: Bearer <access_token>`.

---

## 3. Product Catalog Management (Phase 3)

All product endpoints strictly require authentication and enforce `Product.business_id == current_user.business_id`. Cross-tenant requests return `404 Not Found`.

### `GET /api/v1/products`
Lists products for the authenticated business.

**Query Parameters**:
- `include_inactive` (bool, default `false`): Include soft-deactivated products.
- `category` (string, optional): Filter by product category.
- `search` (string, optional): Search by SKU code or product name.
- `limit` (int, default 100), `offset` (int, default 0): Pagination.

### `POST /api/v1/products`
Manually creates a new product in the store catalog. Enforces unique composite constraint `(business_id, sku)`.

### `GET /api/v1/products/{product_id}`
Retrieves details for a single product.

### `PUT /api/v1/products/{product_id}`
Updates product attributes (`name`, `category`, `unit`, `cost_price`, `selling_price`, `min_stock_level`, `is_active`).

### `DELETE /api/v1/products/{product_id}`
Soft-deactivates the product (`is_active = False`). **Does NOT delete historical sales or product records.**

---

## 4. Sales Analytics & Data Quality Engine (Phase 3)

All analytics endpoints require authentication and scope calculations strictly to `current_user.business_id`.

### `GET /api/v1/analytics/summary`
Returns executive KPI metrics:
- `total_revenue`: Aggregate total sales revenue.
- `observed_units_sold`: Aggregate historical sales volume.
- `avg_revenue_per_recorded_day`: Revenue divided by count of distinct recorded sale dates.
- `active_catalog_size`: Count of active products (`is_active = True`).
- `confirmed_stockout_days`: Count of sales records where `is_stockout = TRUE`.
- `zero_eod_stock_days`: Count of sales records where ending inventory `stock_available = 0`.

**Query Parameters**:
- `range` (string, default `"all"`): Preset range bounds (`7d`, `30d`, `90d`, `1y`, `all`).
- `category` (string, optional): Filter by category.

### `GET /api/v1/analytics/sales-trend`
Returns daily time-series array of `sale_date`, `revenue`, `units_sold`, and `promo_active`.

### `GET /api/v1/analytics/category-breakdown`
Returns revenue distribution grouped by product category with percentage share.

### `GET /api/v1/analytics/top-products`
Returns top N products ranked by total sales revenue.

### `GET /api/v1/analytics/product-performance/{product_id}`
Returns time-series sales, stock level trajectory, and confirmed stockout flags for a single product.

### `GET /api/v1/analytics/data-quality`
Evaluates data completeness, date coverage continuity ratio, missing date gaps count, anomalies count, and operational stockout censoring ratio.

---

## 5. Sales Data Ingestion (Phase 2)

### `POST /api/v1/sales/upload-csv`
Uploads sales CSV file. Executes 2-phase atomic validation. Zero partial writes if any validation error occurs.

### `POST /api/v1/sales/generate-synthetic`
Generates and ingests a 7,300-record synthetic daily sales dataset.

---

## 6. Demand Forecasting Engine & Persistence (Phase 4B)

All forecasting endpoints strictly require authentication and scope calculations to `current_user.business_id`. Cross-tenant requests return `404 Not Found`.

### `POST /api/v1/forecasts/generate`
Triggers demand forecast generation and persistence into PostgreSQL.
- **Request Body**: `{ "product_id": Optional[int] }`
- **Behavior**:
  - Generates 7-day observed demand forecasts relative to `MAX(sale_date)`.
  - Products with $< 28$ recorded sales dates are skipped cleanly and reported in `skipped_products` with reason `"INSUFFICIENT_HISTORY"`.
  - Option A Replacement Strategy: Replaces existing forecast records matching `(business_id, product_id, forecast_date, model_version)`.
- **Response**: `ForecastGenerationResponse` containing `generated_count`, `skipped_count`, `skipped_products`, `metadata` (model_name, model_version, training_cutoff_date, horizon_days, historical_stockout_ratio, disclaimer), and generated forecast records.

### `GET /api/v1/forecasts`
Retrieves persisted demand forecasts for the authenticated business.
- **Query Parameters**: `product_id` (optional int), `start_date` (optional date), `end_date` (optional date).
- **Default Range**: Next 7 forecast days relative to `MAX(forecast_date)`.
- **Response**: `ForecastListResponse`.

### `GET /api/v1/forecasts/product/{product_id}`
Retrieves 7-day demand forecast for a single product.
- **Response**: `ProductForecastResponse` containing `product` info, `metadata`, and 7-day `forecast` points array.

### `GET /api/v1/forecasts/latest`
Retrieves deterministic latest generated forecast set grouped by product for the business.
- **Response**: `LatestForecastResponse`.
