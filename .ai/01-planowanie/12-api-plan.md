# REST API Plan

## 1. Resources

| Resource | Database Table | Description |
| :--- | :--- | :--- |
| **Auth** | `auth_user` | Manages user registration, login, and sessions. |
| **Tags** | `tags` | Represents interest categories (e.g., Art, History) used for AI route generation. |
| **Routes** | `routes` | The core resource representing a user's trip/tour. |
| **Route Points** | `route_points` | Ordered stops within a specific route. |
| **Places** | `places` | Detailed geographic and metadata information for a physical location. |
| **Place Descriptions** | `place_descriptions` | AI-generated content describing a place in the context of the route's theme. |
| **Ratings** | `ratings` | User feedback (thumbs up/down) for routes and descriptions. |

## 2. Endpoints

### 2.1. Authentication
*Standard endpoints (e.g., via `dj-rest-auth`).*

#### **POST** `/api/auth/registration/`
- **Description**: Registers a new user account.
- **Request Payload**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
  }
  ```
- **Response Payload**: User details and auth token.
- **Success**: `201 Created`
- **Error**: `400 Bad Request` (Invalid email, password mismatch, weak password).

#### **POST** `/api/auth/login/`
- **Description**: Authenticates a user and returns a token.
- **Request Payload**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response Payload**: `{"key": "token_string"}`
- **Success**: `200 OK`
- **Error**: `400 Bad Request` (Invalid credentials).

#### **POST** `/api/auth/logout/`
- **Description**: Invalidates the current user's session/token.
- **Success**: `200 OK`

### 2.2. Tags

#### **GET** `/api/tags/`
- **Description**: Retrieves the list of available interest tags for route generation.
- **Query Parameters**: None.
- **Response Payload**:
  ```json
  [
    {
      "id": 1,
      "name": "History",
      "description": "Historical landmarks and museums",
      "is_active": true
    }
  ]
  ```
- **Success**: `200 OK`

### 2.3. Routes

#### **GET** `/api/routes/`
- **Description**: Lists routes belonging to the authenticated user.
- **Query Parameters**:
  - `page`: Integer (pagination).
  - `status`: String (`temporary`, `saved`). Default: `saved`.
  - `ordering`: String (e.g., `-created_at`).
- **Response Payload**:
  ```json
  {
    "count": 15,
    "next": "...",
    "previous": null,
    "results": [
      {
        "id": 101,
        "name": "Warsaw Old Town",
        "status": "saved",
        "route_type": "ai_generated",
        "created_at": "2024-01-01T12:00:00Z",
        "points_count": 5
      }
    ]
  }
  ```
- **Success**: `200 OK`

#### **POST** `/api/routes/`
- **Description**: Creates a new route. Supports both "AI Generated" and "Manual" initialization.
- **Request Payload (AI Mode)**:
  ```json
  {
    "route_type": "ai_generated",
    "tags": [1, 3], /* IDs of selected tags (1-3 tags) */
    "description": "I want to visit hidden architectural gems." /* Optional, 1000-10000 chars */
  }
  ```
- **Request Payload (Manual Mode)**:
  ```json
  {
    "route_type": "manual",
    "name": "My Custom Trip" /* Optional */
  }
  ```
- **Response Payload**: The created route object. For AI mode, this might take time; considered asynchronous in backend, but for MVP may return the generated route directly or a "processing" status if using background tasks. Designed here as synchronous for MVP simplicity but prepared for `temporary` status.
- **Success**: `201 Created`
- **Error**: `400 Bad Request` (Validation errors, e.g., too many tags).

#### **GET** `/api/routes/{id}/`
- **Description**: Retrieves full details of a specific route, including ordered points and their descriptions. Optimized for offline caching.
- **Response Payload**:
  ```json
  {
    "id": 101,
    "name": "Warsaw Old Town",
    "status": "temporary",
    "route_type": "ai_generated",
    "user_rating_value": 1, /* Current user's rating if any */
    "points": [
      {
        "id": 501,
        "order": 1,
        "place": {
          "id": 200,
          "name": "Royal Castle",
          "lat": 52.248,
          "lon": 21.015,
          "address": "Plac Zamkowy 4"
        },
        "description": {
          "id": 901,
          "content": "A detailed AI-generated story..."
        }
      }
    ]
  }
  ```
- **Success**: `200 OK`
- **Error**: `404 Not Found` (If route doesn't exist or belongs to another user).

#### **PATCH** `/api/routes/{id}/`
- **Description**: Updates route details, primarily for saving a temporary route or renaming.
- **Request Payload**:
  ```json
  {
    "status": "saved", /* Transitions from temporary to saved */
    "name": "My Official Trip Name"
  }
  ```
- **Success**: `200 OK`
- **Error**: `400 Bad Request`

#### **DELETE** `/api/routes/{id}/`
- **Description**: Deletes a route and its associated points/descriptions/ratings (via Cascade).
- **Success**: `204 No Content`

#### **POST** `/api/routes/{id}/optimize/`
- **Description**: Triggers the route optimization algorithm to reorder points. Only allowed for `manual` routes.
- **Request Payload**: Empty or config parameters.
- **Response Payload**: List of reordered route points (same structure as in `GET /routes/{id}/`).
- **Success**: `200 OK`
- **Error**: `400 Bad Request` (If route is not manual or has too few points).

### 2.4. Route Points

#### **POST** `/api/routes/{id}/points/`
- **Description**: Adds a new point to a manual route. Automatically creates the `Place` if it doesn't exist locally (lookup by OSM/Wikipedia ID implied).
- **Request Payload**:
  ```json
  {
    "place": {
      "name": "Palace of Culture",
      "lat": 52.231,
      "lon": 21.006,
      "osm_id": 123456, /* Optional but recommended for deduplication */
      "address": "Plac Defilad 1"
    }
  }
  ```
- **Response Payload**: created point definition.
- **Success**: `201 Created`
- **Error**: `400 Bad Request` (Max points limit reached).

#### **DELETE** `/api/routes/{id}/points/{point_id}/`
- **Description**: Removes a point from the route.
- **Success**: `204 No Content`

### 2.5. Ratings

#### **POST** `/api/ratings/`
- **Description**: UPSERTS a user's rating for a route or a place description.
- **Request Payload**:
  ```json
  {
    "rating_type": "route", /* 'route' or 'place_description' */
    "rating_value": 1, /* 1 (positive) or -1 (negative) */
    "route_id": 101, /* Required if type is route */
    "place_description_id": null /* Required if type is place_description */
  }
  ```
- **Success**: `201 Created` (or `200 OK` if updated).
- **Error**: `400 Bad Request` (Invalid values or missing IDs).

## 3. Authentication and Authorization

- **Mechanism**: **JSON Web Token (JWT)**.
  - Ideally implemented using `djangorestframework-simplejwt`.
  - Clients must include `Authorization: Bearer <token>` in headers.
- **Authorization Scopes**:
  - `AllowAny`: For Registration/Login.
  - `IsAuthenticated`: For all other endpoints.
  - `IsOwner` (Custom Class): Ensures users can only access/modify their own Resources (Routes, Ratings).
    - **RLS Confirmation**: The API logic must align with Database Row Level Security polices (user_id check). Django `queryset.filter(user=request.user)` will be the primary application-level enforcement.

## 4. Validation and Business Logic

### Validation Rules
- **Routes**:
  - `tags`:
    - Min: 1
    - Max: 3
    - Required if `route_type` is `ai_generated`.
  - `status`: Must be one of `['temporary', 'saved']`.
  - `route_type`: Immutable. Must be `['ai_generated', 'manual']`.
- **Place Content**:
  - `content`: Length constraint 2500 - 5000 characters (enforced by DB check and Serializer).
- **Coordinates**:
  - `lat`: -90 to 90.
  - `lon`: -180 to 180.

### Business Logic Implementation
1. **Route Generation Limit**:
   - **AI**: Max 7 points per route.
   - **Manual**: Max 10 points per route.
   - **Implementation**: Check point count in `perform_create` (add point) or within the AI generation service.
2. **AI Generation Flow**:
   - When `POST /routes/` is called with `ai_generated`, the backend calls the LLM service (OpenRouter).
   - Generated places are matched against the `places` table (deduplication via `osm_id`/`wikipedia_id`).
   - `place_descriptions` are created linked to route points.
   - Initial status is `temporary`.
3. **Draft Cleanup**:
   - `temporary` routes are not typically returned in the default `GET /routes/` list unless specifically filtered with `?status=temporary` (or handled via periodic cleanup tasks).
4. **Ratings Uniqueness**:
   - A user can rate a specific target (route/description) only once.
   - `POST` to ratings endpoint acts as an UPSERT (update if exists).
