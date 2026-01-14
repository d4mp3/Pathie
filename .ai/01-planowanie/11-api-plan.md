# REST API Plan

## 1. Resources
| Resource | Database Table | Description |
| :--- | :--- | :--- |
| **Auth** | `auth_user` | User authentication and account management. |
| **Tags** | `tags` | Predefined interest tags (e.g., Art, History). |
| **Routes** | `routes` | The main resource representing a tour/trip. |
| **Route Points** | `route_points` | Individual stops within a route. |
| **Places** | `places` | Geographic data and metadata for specific locations. |
| **Place Descriptions** | `place_descriptions` | AI-generated descriptions for route points. |
| **Ratings** | `ratings` | User ratings for routes and descriptions. |

## 2. Endpoints

### 2.1. Authentication (Auth)
*Standard endpoints provided by `dj-rest-auth` or similar.*

- **POST /api/auth/registration/**
  - **Description**: Register a new user.
- **POST /api/auth/login/**
  - **Description**: Log in with email and password (returns token).
- **POST /api/auth/logout/**
  - **Description**: Log out the current user.

### 2.2. Tags
**GET /api/tags/**
- **Description**: Retrieve a list of available interest tags.
- **HTTP Method**: `GET`
- **Query Parameters**: None
- **Response JSON**:
  ```json
  [
    {
      "id": 1,
      "name": "History",
      "description": "Historical sites and monuments",
      "icon_url": "https://example.com/icons/history.png"
    }
  ]
  ```

### 2.3. Routes

**GET /api/routes/**
- **Description**: Retrieve a list of saved routes for the logged-in user.
- **HTTP Method**: `GET`
- **Query Parameters**:
  - `page` (integer): Page number for pagination.
  - `status` (string, optional): Filter by status (e.g., `saved`, `temporary`). Default: `saved`.
- **Response JSON**:
  ```json
  {
    "count": 10,
    "next": "http://api.example.com/routes/?page=2",
    "previous": null,
    "results": [
      {
        "id": 101,
        "name": "Krakow Tour",
        "status": "saved",
        "route_type": "ai_generated",
        "created_at": "2024-05-20T10:00:00Z",
        "thumbnail_url": "..."
      }
    ]
  }
  ```

**POST /api/routes/**
- **Description**: Create a new route. Supports two modes:
  1. **AI Generated**: Accepts tags and description, triggers generation details.
  2. **Manual**: Creates an empty route for manual point addition.
- **Request JSON (AI Mode)**:
  ```json
  {
    "route_type": "ai_generated",
    "tags": [1, 2], // List of Tag IDs
    "description": "I want to see medieval walls and hidden gems."
  }
  ```
- **Request JSON (Manual Mode)**:
  ```json
  {
    "route_type": "manual",
    "name": "My Custom Trip" // Optional
  }
  ```
- **Success Response**: `201 Created` with the route object.
- **Error Response**: `400 Bad Request` (Validation errors).

**GET /api/routes/{id}/**
- **Description**: Retrieve detailed information about a specific route, including ordered points and descriptions.
- **HTTP Method**: `GET`
- **Response JSON**:
  ```json
  {
    "id": 101,
    "name": "Krakow Tour",
    "status": "temporary",
    "route_type": "ai_generated",
    "points": [
      {
        "id": 501,
        "place": {
          "name": "Wawel Castle",
          "lat": 50.054,
          "lon": 19.935,
          "address": "Wawel 5"
        },
        "order": 1,
        "description": {
          "id": 901,
          "content": "The Wawel Castle is..."
        }
      }
    ]
  }
  ```

**PATCH /api/routes/{id}/**
- **Description**: Update route details (e.g., change name, save route by changing status).
- **HTTP Method**: `PATCH`
- **Request JSON**:
  ```json
  {
    "status": "saved",
    "name": "My Awesome Trip"
  }
  ```
- **Success Response**: `200 OK`

**DELETE /api/routes/{id}/**
- **Description**: Delete a route.
- **HTTP Method**: `DELETE`
- **Success Response**: `204 No Content`

**POST /api/routes/{id}/optimize/**
- **Description**: Triggers automatic optimization of point order (Manual mode).
- **HTTP Method**: `POST`
- **Response JSON**: Updated list of route points.

### 2.4. Route Points (Manual Mode)

**POST /api/routes/{id}/points/**
- **Description**: Add a new point to a manual route. Can create a `Place` if it doesn't exist.
- **HTTP Method**: `POST`
- **Request JSON**:
  ```json
  {
    "name": "Cloth Hall",
    "lat": 50.061,
    "lon": 19.937,
    "osm_id": 12345, // Optional
    "address": "Rynek Główny 1"
  }
  ```
- **Success Response**: `201 Created`

**DELETE /api/routes/{id}/points/{point_id}/**
- **Description**: Remove a point from the route.
- **HTTP Method**: `DELETE`
- **Success Response**: `204 No Content`

### 2.5. Ratings

**POST /api/ratings/**
- **Description**: Submit a rating for a route or a place description.
- **HTTP Method**: `POST`
- **Request JSON**:
  ```json
  {
    "rating_type": "route", // or "place_description"
    "rating_value": 1, // 1 (like/smile) or -1 (dislike/sad)
    "route_id": 101, // Required if type is route
    "place_description_id": null // Required if type is place_description
  }
  ```
- **Success Response**: `201 Created`

## 3. Authentication and Authorization

### Mechanism
- **Token-Based**: JWT (JSON Web Tokens) via `djangorestframework-simplejwt`.
- **Flow**: Client exchanges credentials for Access/Refresh tokens. Access token sent in `Authorization: Bearer <token>` header.

### Permissions
1. **IsAuthenticated**: Required for creating routes, saving, viewing own routes, and rating.
2. **IsOwner**: Custom permission to ensure users can only view/edit/delete their own routes (`route.user == request.user`).
3. **AllowAny**: Public access for Registration and Login endpoints.

## 4. Validation and Business Logic

### Validation Rules
- **Routes**:
  - `status`: Must be `'temporary'` or `'saved'`.
  - `route_type`: Immutable after creation.
  - `tags`: Minimum 1, Maximum 3 tags for AI generation.
  - `description`: Maximum 10,000 characters.
- **Route Points**:
  - `lat`: Must be between -90 and 90.
  - `lon`: Must be between -180 and 180.
- **Ratings**:
  - `rating_value`: Must be `1` or `-1`.

### Business Logic
- **Point Limits**:
  - Manual routes: Max 10 points. Enforced by API before adding a point.
  - AI routes: Generated with max 7 points.
- **Optimization**:
  - Manual optimization requests trigger a spatial sorting algorithm (e.g., TSP approximation) to reorder points.
- **Security**:
  - API querysets are filtered by `request.user` to prevent data leakage.
  - Rate limiting applied to AI generation endpoints to control costs.
