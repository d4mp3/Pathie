# API Routes List Endpoint - Manual Testing Guide

## Endpoint Details
- **URL**: `http://localhost:8000/api/routes/`
- **Method**: `GET`
- **Content-Type**: `application/json`
- **Authentication**: Required (Token-based)

## Prerequisites
You need a valid authentication token. Obtain one by logging in:

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

Save the returned token key for use in the `Authorization` header.

---

## Test Case 1: Successful Request with Default Parameters

### Request
```bash
curl -X GET http://localhost:8000/api/routes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 6,
      "name": "Saved Route 5",
      "status": "saved",
      "route_type": "ai_generated",
      "created_at": "2026-01-22T22:13:16.815132+01:00",
      "points_count": 3
    },
    {
      "id": 5,
      "name": "Saved Route 4",
      "status": "saved",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.800112+01:00",
      "points_count": 3
    }
  ]
}
```

**Notes**:
- Default filter: `status=saved`
- Default ordering: `-created_at` (newest first)
- Default pagination: 10 items per page

---

## Test Case 2: Unauthorized Access

### Request
```bash
curl -X GET http://localhost:8000/api/routes/ \
  -H "Content-Type: application/json"
```

### Expected Response (401 Unauthorized)
```json
{
  "detail": "Nie podano danych uwierzytelniających."
}
```

---

## Test Case 3: Filter by Status (Temporary)

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?status=temporary" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 9,
      "name": "Temporary Route 3",
      "status": "temporary",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.848400+01:00",
      "points_count": 1
    },
    {
      "id": 8,
      "name": "Temporary Route 2",
      "status": "temporary",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.838795+01:00",
      "points_count": 1
    }
  ]
}
```

**Notes**:
- Only routes with `status=temporary` are returned

---

## Test Case 4: Invalid Status Filter (Fallback to Default)

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?status=invalid_status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 6,
      "name": "Saved Route 5",
      "status": "saved",
      "route_type": "ai_generated",
      "created_at": "2026-01-22T22:13:16.815132+01:00",
      "points_count": 3
    }
  ]
}
```

**Notes**:
- Invalid status values fallback to default `saved`
- This prevents errors and ensures consistent behavior

---

## Test Case 5: Ordering by Name (Ascending)

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?status=saved&ordering=name" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "name": "Saved Route 1",
      "status": "saved",
      "route_type": "ai_generated",
      "created_at": "2026-01-22T22:13:16.681417+01:00",
      "points_count": 3
    },
    {
      "id": 3,
      "name": "Saved Route 2",
      "status": "saved",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.747118+01:00",
      "points_count": 3
    }
  ]
}
```

**Notes**:
- Routes are ordered alphabetically by name
- Use `-name` for descending order

---

## Test Case 6: Ordering by Points Count (Descending)

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?status=temporary&ordering=-points_count" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 7,
      "name": "Temporary Route 1",
      "status": "temporary",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.827998+01:00",
      "points_count": 1
    },
    {
      "id": 1,
      "name": "Test Route",
      "status": "temporary",
      "route_type": "manual",
      "created_at": "2026-01-22T21:26:12.166168+01:00",
      "points_count": 0
    }
  ]
}
```

**Notes**:
- Routes with more points appear first
- The `points_count` annotation automatically excludes removed points (`is_removed=True`)

---

## Test Case 7: Pagination (Page 1, Size 2)

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?page=1&page_size=2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 5,
  "next": "http://localhost:8000/api/routes/?page=2&page_size=2",
  "previous": null,
  "results": [
    {
      "id": 6,
      "name": "Saved Route 5",
      "status": "saved",
      "route_type": "ai_generated",
      "created_at": "2026-01-22T22:13:16.815132+01:00",
      "points_count": 3
    },
    {
      "id": 5,
      "name": "Saved Route 4",
      "status": "saved",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.800112+01:00",
      "points_count": 3
    }
  ]
}
```

**Notes**:
- Only 2 results returned per page
- `next` link provides URL for the next page
- Total count is available in the `count` field

---

## Test Case 8: Pagination (Page 2, Size 2)

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?page=2&page_size=2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 5,
  "next": "http://localhost:8000/api/routes/?page=3&page_size=2",
  "previous": "http://localhost:8000/api/routes/?page_size=2",
  "results": [
    {
      "id": 4,
      "name": "Saved Route 3",
      "status": "saved",
      "route_type": "ai_generated",
      "created_at": "2026-01-22T22:13:16.777144+01:00",
      "points_count": 3
    },
    {
      "id": 3,
      "name": "Saved Route 2",
      "status": "saved",
      "route_type": "manual",
      "created_at": "2026-01-22T22:13:16.747118+01:00",
      "points_count": 3
    }
  ]
}
```

**Notes**:
- Both `next` and `previous` links are provided
- Navigation through pages is seamless

---

## Test Case 9: Page Out of Range

### Request
```bash
curl -X GET "http://localhost:8000/api/routes/?page=999" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Expected Response (404 Not Found)
```json
{
  "detail": "Invalid page."
}
```

**Notes**:
- Requesting a non-existent page returns 404
- DRF's PageNumberPagination handles this automatically

---

## Test Case 10: Data Isolation Between Users

### Setup
Create a second user and obtain their token:
```bash
# Login as second user
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user2@example.com",
    "password": "testpass123"
  }'
```

### Request (User 2 - No Routes)
```bash
curl -X GET http://localhost:8000/api/routes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token USER2_TOKEN_HERE"
```

### Expected Response (200 OK)
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

**Notes**:
- Each user only sees their own routes
- Data isolation is enforced at the database query level

---

## Performance Verification

### SQL Query Analysis

The endpoint uses a single optimized SQL query with:
- **LEFT OUTER JOIN** on `route_points`
- **COUNT with FILTER** for points_count annotation
- **WHERE** clause for user and status filtering
- **GROUP BY** for aggregation
- **ORDER BY** for sorting

**Expected Query Count**: 1 query per request (no N+1 problem)

### Example Query
```sql
SELECT 
  "routes"."id", 
  "routes"."user_id", 
  "routes"."name", 
  "routes"."status", 
  "routes"."route_type", 
  "routes"."created_at", 
  COUNT("route_points"."id") FILTER (WHERE NOT "route_points"."is_removed") AS "points_count" 
FROM "routes" 
LEFT OUTER JOIN "route_points" ON ("routes"."id" = "route_points"."route_id") 
WHERE ("routes"."user_id" = 1 AND "routes"."status" = 'saved') 
GROUP BY "routes"."id" 
ORDER BY "routes"."created_at" DESC;
```

---

## Available Query Parameters

| Parameter | Type | Default | Description | Valid Values |
|-----------|------|---------|-------------|--------------|
| `page` | integer | 1 | Page number for pagination | 1+ |
| `page_size` | integer | 10 | Number of items per page | 1-100 |
| `status` | string | `saved` | Filter routes by status | `saved`, `temporary` |
| `ordering` | string | `-created_at` | Field to order results by | `created_at`, `-created_at`, `name`, `-name`, `status`, `-status`, `route_type`, `-route_type`, `points_count`, `-points_count` |

**Notes**:
- Prefix field name with `-` for descending order
- Invalid values fallback to defaults without error

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of routes matching filters |
| `next` | string/null | URL for the next page (null if no more pages) |
| `previous` | string/null | URL for the previous page (null if first page) |
| `results` | array | Array of route objects |
| `results[].id` | integer | Unique route identifier |
| `results[].name` | string | Route name |
| `results[].status` | string | Route status (`saved` or `temporary`) |
| `results[].route_type` | string | Route type (`ai_generated` or `manual`) |
| `results[].created_at` | string | ISO 8601 timestamp of creation |
| `results[].points_count` | integer | Number of active points (excludes removed) |

---

## Common Error Responses

### 401 Unauthorized
```json
{
  "detail": "Nie podano danych uwierzytelniających."
}
```
**Cause**: Missing or invalid authentication token

### 404 Not Found
```json
{
  "detail": "Invalid page."
}
```
**Cause**: Requested page number exceeds available pages

---

## Testing Checklist

- [ ] Successful request with authentication returns 200
- [ ] Unauthorized request returns 401
- [ ] Default filter returns only saved routes
- [ ] Filter by temporary status works correctly
- [ ] Invalid status falls back to saved (default)
- [ ] Ordering by name (ascending and descending) works
- [ ] Ordering by points_count works
- [ ] Ordering by created_at works
- [ ] Pagination works correctly
- [ ] Page links (next/previous) are valid
- [ ] Out of range page returns 404
- [ ] Data isolation: users only see their own routes
- [ ] points_count excludes removed points
- [ ] Performance: single SQL query (no N+1)

---

## Docker Testing Commands

If running in Docker, prefix curl commands with container access:

```bash
# Check container status
docker ps

# Test from host machine
curl -X GET http://localhost:8000/api/routes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE"

# Access Django shell for data inspection
docker compose exec app python manage.py shell
```
