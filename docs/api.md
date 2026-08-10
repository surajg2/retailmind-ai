# REST API Specification — RetailMind AI (Phase 1)

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
  "timestamp": "2026-08-10T22:00:00Z"
}
```

---

## 2. Authentication Flow

### `POST /api/v1/auth/register`
Registers a new user and associated store business entity. Password is automatically hashed using `bcrypt`.

**Request Body**:
```json
{
  "email": "owner@store.com",
  "password": "SecurePassword123!",
  "full_name": "Suraj Gupta",
  "business_name": "Suraj Kirana Store",
  "business_type": "Kirana / General Store"
}
```

**Response `201 Created`**:
```json
{
  "id": 1,
  "email": "owner@store.com",
  "full_name": "Suraj Gupta",
  "role": "owner",
  "is_active": true,
  "business_id": 1,
  "business": {
    "id": 1,
    "name": "Suraj Kirana Store",
    "type": "Kirana / General Store",
    "location": null,
    "created_at": "2026-08-10T22:00:00Z"
  },
  "created_at": "2026-08-10T22:00:00Z"
}
```

---

### `POST /api/v1/auth/login`
Authenticates email and password, returning a JWT access token.

**Request Body**:
```json
{
  "email": "owner@store.com",
  "password": "SecurePassword123!"
}
```

**Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### `GET /api/v1/auth/me`
Protected endpoint retrieving profile of authenticated user.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response `200 OK`**:
```json
{
  "id": 1,
  "email": "owner@store.com",
  "full_name": "Suraj Gupta",
  "role": "owner",
  "is_active": true,
  "business_id": 1,
  "business": {
    "id": 1,
    "name": "Suraj Kirana Store",
    "type": "Kirana / General Store"
  }
}
```

**Error Response `401 Unauthorized`**:
```json
{
  "detail": "Could not validate credentials"
}
```
