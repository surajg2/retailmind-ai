# REST API Specification — RetailMind AI (Phase 1 & Phase 2)

Base URL: `http://localhost:8000`  
API Version Prefix: `/api/v1`

---

## 1. Health Monitoring

### `GET /health`
Verifies backend server status and PostgreSQL database connectivity.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-08-12T21:40:00Z"
}
```

---

## 2. Authentication Flow

### `POST /api/v1/auth/register`
Registers a new user and associated store business entity. Password is automatically hashed using `bcrypt`.

### `POST /api/v1/auth/login`
Authenticates email and password, returning a JWT access token.

### `GET /api/v1/auth/me`
Protected endpoint retrieving profile of authenticated user. Requires `Authorization: Bearer <access_token>`.

---

## 3. Sales Data & Ingestion Endpoints (Phase 2)

### `POST /api/v1/sales/upload-csv`
Protected endpoint for uploading a sales CSV file. Executes 2-phase atomic validation and database ingestion. If ANY validation error occurs, ZERO rows are written to PostgreSQL.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Body**: `file` (CSV file)

**Response `200 OK` (Successful Atomic Import)**:
```json
{
  "success": true,
  "total_rows_processed": 7300,
  "successful_imports": 7300,
  "errors": [],
  "message": "Successfully imported 7300 sales records into PostgreSQL database."
}
```

**Response `200 OK` (Validation Rejection / Zero Rows Written)**:
```json
{
  "success": false,
  "total_rows_processed": 100,
  "successful_imports": 0,
  "errors": [
    {
      "row_number": 14,
      "column": "selling_price",
      "error": "Invalid monetary value '-25.00'. Selling price must be greater than 0.00."
    },
    {
      "row_number": 42,
      "column": "product_name",
      "error": "SKU metadata conflict for 'SKU-GROC-001': existing product name 'Atta 5kg' vs CSV 'Atta 10kg'."
    }
  ],
  "message": "Import failed with 2 validation errors. Zero rows were inserted into the database."
}
```

---

### `POST /api/v1/sales/generate-synthetic`
Generates a 7,300-record synthetic daily sales dataset (20 products x 365 days) and automatically ingests it into PostgreSQL for the current user's business.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response `201 Created`**:
```json
{
  "success": true,
  "records_generated": 7300,
  "imported_count": 7300,
  "message": "Successfully generated and imported 7300 synthetic daily sales records."
}
```

---

### `GET /api/v1/sales`
Retrieves a paginated list of sales records for the authenticated user's store.

**Query Parameters**:
- `limit` (int, default 100): Page size limit (1–1000).
- `offset` (int, default 0): Pagination offset.
- `sku` (string, optional): Filter by product SKU.

**Response `200 OK`**:
```json
[
  {
    "id": 1,
    "business_id": 1,
    "product_id": 1,
    "quantity": 39,
    "selling_price": "245.00",
    "total_amount": "9555.00",
    "promotion": false,
    "holiday": false,
    "festival": null,
    "stock_available": 132,
    "is_stockout": null,
    "sale_date": "2025-01-01",
    "created_at": "2026-08-12T21:40:00Z",
    "product": {
      "id": 1,
      "business_id": 1,
      "sku": "SKU-GROC-001",
      "name": "Aashirvaad Whole Wheat Atta 5kg",
      "category": "Atta & Flours",
      "unit": "pcs",
      "cost_price": "171.50",
      "selling_price": "245.00",
      "min_stock_level": 10,
      "created_at": "2026-08-12T21:40:00Z"
    }
  }
]
```
