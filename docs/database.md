# PostgreSQL Database Specification — RetailMind AI

RetailMind AI uses **PostgreSQL** managed via **SQLAlchemy ORM** and **Alembic migrations**.

---

## Entity Relationship Summary

```
Business (1) <------- (N) User
Business (1) <------- (N) Product
Business (1) <------- (N) Sales
Business (1) <------- (N) Inventory
Business (1) <------- (N) Prediction
Business (1) <------- (N) Recommendation

Product (1) <------- (N) Sales
Product (1) <------- (1) Inventory
Product (1) <------- (N) Prediction
Product (1) <------- (N) Recommendation
```

---

## Table Schemas (Phase 1 & Phase 2 Implemented)

### 1. `businesses`
* `id` (INT, PK)
* `name` (VARCHAR(255), NOT NULL)
* `type` (VARCHAR(100))
* `location` (VARCHAR(255))
* `created_at` (TIMESTAMPTZ)
* `updated_at` (TIMESTAMPTZ)

### 2. `users`
* `id` (INT, PK)
* `email` (VARCHAR(255), UNIQUE, INDEX, NOT NULL)
* `hashed_password` (VARCHAR(255), NOT NULL) — *Bcrypt hash, plain text passwords strictly prohibited*
* `full_name` (VARCHAR(255))
* `role` (VARCHAR(50), DEFAULT 'owner')
* `is_active` (BOOLEAN, DEFAULT TRUE)
* `business_id` (INT, FK -> `businesses.id` ON DELETE CASCADE)
* `created_at` (TIMESTAMPTZ)
* `updated_at` (TIMESTAMPTZ)

### 3. `products`
* `id` (INT, PK)
* `business_id` (INT, FK -> `businesses.id` ON DELETE CASCADE)
* `sku` (VARCHAR(100), INDEX, NOT NULL)
* `name` (VARCHAR(255), INDEX, NOT NULL)
* `category` (VARCHAR(100), INDEX)
* `unit` (VARCHAR(50), DEFAULT 'pcs')
* `cost_price` (NUMERIC(10,2), DEFAULT 0.00, NOT NULL) — *Exact monetary type*
* `selling_price` (NUMERIC(10,2), DEFAULT 0.00, NOT NULL) — *Exact monetary type*
* `min_stock_level` (INT, DEFAULT 10)
* `created_at` (TIMESTAMPTZ)
* `updated_at` (TIMESTAMPTZ)
* **Index**: Composite Unique Index (`business_id`, `sku`)

### 4. `sales` (Phase 2 Daily Sales Table)
* `id` (INT, PK)
* `business_id` (INT, FK -> `businesses.id` ON DELETE CASCADE)
* `product_id` (INT, FK -> `products.id` ON DELETE CASCADE)
* `quantity` (INT, NOT NULL) — *units_sold on date*
* `selling_price` (NUMERIC(10,2), NOT NULL) — *Exact monetary per-unit price*
* `total_amount` (NUMERIC(10,2), NOT NULL) — *units_sold * selling_price*
* `promotion` (BOOLEAN, DEFAULT FALSE) — *Promo active indicator*
* `holiday` (BOOLEAN, DEFAULT FALSE) — *Public holiday indicator*
* `festival` (VARCHAR(100), NULLABLE) — *Festival name or NULL*
* `stock_available` (INT, DEFAULT 0) — *Observed end-of-day stock level*
* `is_stockout` (BOOLEAN, NULLABLE, INDEX) — *Derived indicator for demand censoring*
* `sale_date` (DATE, INDEX, NOT NULL) — *PostgreSQL DATE type for daily aggregation*
* `created_at` (TIMESTAMPTZ)
* **Index**: Composite Unique Index `idx_sales_business_product_date` (`business_id`, `product_id`, `sale_date`)

### 5. `inventory`
* `id` (INT, PK)
* `business_id` (INT, FK -> `businesses.id` ON DELETE CASCADE)
* `product_id` (INT, UNIQUE, FK -> `products.id` ON DELETE CASCADE)
* `current_stock` (INT, DEFAULT 0)
* `reorder_point` (INT, DEFAULT 15)
* `last_restocked_at` (TIMESTAMPTZ)
* `updated_at` (TIMESTAMPTZ)

### 6. `festivals`
* `id` (INT, PK)
* `name` (VARCHAR(100), INDEX, NOT NULL)
* `start_date` (TIMESTAMPTZ, INDEX, NOT NULL)
* `end_date` (TIMESTAMPTZ, NOT NULL)
* `region` (VARCHAR(100), DEFAULT 'National')
* `expected_uplift` (FLOAT, DEFAULT 1.2)
* `created_at` (TIMESTAMPTZ)

### 7. `predictions`
* `id` (INT, PK)
* `business_id` (INT, FK -> `businesses.id` ON DELETE CASCADE)
* `product_id` (INT, FK -> `products.id` ON DELETE CASCADE)
* `model_version` (VARCHAR(50), DEFAULT 'v1.0')
* `predicted_demand` (FLOAT, NOT NULL)
* `prediction_date` (TIMESTAMPTZ, INDEX, NOT NULL)
* `created_at` (TIMESTAMPTZ)

### 8. `recommendations`
* `id` (INT, PK)
* `business_id` (INT, FK -> `businesses.id` ON DELETE CASCADE)
* `product_id` (INT, FK -> `products.id` ON DELETE CASCADE)
* `recommendation_type` (VARCHAR(100), INDEX, NOT NULL)
* `details` (TEXT)
* `status` (VARCHAR(50), DEFAULT 'PENDING')
* `created_at` (TIMESTAMPTZ)

---

## Migration History

1. `001_initial_schema.py`: Base tables creation.
2. `002_sales_phase2_schema.py`: Sales table alteration (`Date` sale_date, `Numeric(10,2)` money fields, `is_stockout`, unique constraint on `business_id` + `product_id` + `sale_date`).
