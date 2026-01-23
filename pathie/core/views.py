import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model, logout
from django.db import transaction
from django.db.models import Prefetch, Subquery, OuterRef, IntegerField
from django.shortcuts import get_object_or_404
from typing import Any

from .serializers import (
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer,
    RatingSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    RouteCreateSerializer,
    RouteUpdateSerializer,
    RouteOptimizeInputSerializer,
    RoutePointDetailSerializer,
    RoutePointCreateSerializer,
    RoutePointSerializer,
    TagSerializer,
)
from .models import Rating, Route, RoutePoint, Tag
from .selectors import route_list_selector
from .services import RouteService, BusinessLogicException
from .permissions import IsRouteOwner

User = get_user_model()
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Tag Views
# -----------------------------------------------------------------------------


class TagListView(generics.ListAPIView):
    """
    API endpoint for retrieving a list of available interest tags.

    Returns all active tags that can be used when generating AI routes.
    Tags are ordered by priority (descending) and name (ascending).

    **Endpoint:** GET /api/tags/

    **Required Headers:**
    - Authorization: Token <token_key>

    **Query Parameters:** None

    **Success Response (200 OK):**
    ```json
    [
        {
            "id": 1,
            "name": "History",
            "description": "Historical landmarks and museums",
            "is_active": true
        },
        {
            "id": 2,
            "name": "Nature",
            "description": "Parks, gardens, and natural attractions",
            "is_active": true
        }
    ]
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Read-only endpoint (GET only)
    - Returns only active tags (is_active=True)

    **Performance:**
    - No pagination (returns flat array)
    - Small dataset (typically < 20 tags)
    - Can be cached for 1 hour (tags rarely change)
    - Ordered by priority and name for consistent display
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    pagination_class = None  # Disable pagination to return flat array

    def get_queryset(self):
        """
        Return all active tags ordered by priority and name.

        Returns:
            QuerySet[Tag]: Active tags ordered by priority (desc) and name (asc)
        """
        return Tag.objects.filter(is_active=True).order_by('-priority', 'name')


# -----------------------------------------------------------------------------
# Authentication Views
# -----------------------------------------------------------------------------


class RegistrationAPIView(APIView):
    """
    API endpoint for user registration.

    Accepts email and password, validates data, creates new user account,
    and returns an authentication token for immediate API access.

    **Endpoint:** POST /api/auth/registration/

    **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "securepassword123",
        "password_confirm": "securepassword123"
    }
    ```

    **Success Response (201 Created):**
    ```json
    {
        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
        "user_id": 1,
        "email": "user@example.com"
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "email": ["Użytkownik z tym adresem email już istnieje."],
        "password_confirm": ["Hasła nie są identyczne."]
    }
    ```
    or
    ```json
    {
        "password": [
            "To hasło jest zbyt krótkie. Musi zawierać co najmniej 8 znaków.",
            "To hasło jest zbyt powszechne."
        ]
    }
    ```

    **Security Features:**
    - Rate limiting: 5 requests per minute for anonymous users
    - Password strength validation using Django's validators
    - Email uniqueness validation
    - Automatic password hashing
    - Transaction atomic to ensure data consistency
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = RegistrationSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Handles POST requests for user registration.

        Args:
            request: HTTP request object containing email, password, and password_confirm

        Returns:
            Response: JSON response with authentication token and user data or error messages
                     - 201 Created if registration successful
                     - 400 Bad Request for validation errors
        """
        serializer = self.serializer_class(data=request.data)

        # Validate input data
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create new user
        user = serializer.save()

        # Get the authentication token (created in serializer)
        token = Token.objects.get(user=user)

        # Prepare response data
        user_serializer = UserSerializer(user)
        response_data = {
            "token": token.key,
            **user_serializer.data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """
    API endpoint for user authentication.

    Accepts email and password, validates credentials, and returns an authentication token.

    **Endpoint:** POST /api/auth/login/

    **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    ```

    **Success Response (200 OK):**
    ```json
    {
        "key": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "email": ["Adres e-mail jest wymagany."],
        "password": ["Hasło jest wymagane."]
    }
    ```
    or
    ```json
    {
        "non_field_errors": ["Nieprawidłowy adres e-mail lub hasło."]
    }
    ```

    **Security Features:**
    - Rate limiting: 5 requests per minute for anonymous users
    - Password validation using Django's secure check_password method
    - Generic error messages to prevent user enumeration
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = LoginSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Handles POST requests for user login.

        Args:
            request: HTTP request object containing email and password

        Returns:
            Response: JSON response with authentication token or error messages
        """
        serializer = self.serializer_class(data=request.data)

        # Validate credentials
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get authenticated user from validated data
        user = serializer.validated_data["user"]

        # Get or create authentication token for the user
        token, created = Token.objects.get_or_create(user=user)

        # Return token in the expected format
        return Response({"key": token.key}, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.

    Invalidates the user's authentication token and clears the Django session.

    **Endpoint:** POST /api/auth/logout/

    **Required Headers:**
    - Authorization: Token <token_key>

    **Request Body:** Empty

    **Success Response (200 OK):**
    ```json
    {
        "detail": "Pomyślnie wylogowano."
    }
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Deletes the authentication token from database
    - Clears Django session for hybrid browser/API access
    - Uses POST method to prevent CSRF attacks and browser pre-fetching
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Handles POST requests for user logout.

        Args:
            request: HTTP request object with authenticated user

        Returns:
            Response: JSON response confirming successful logout
        """
        try:
            # Delete the authentication token
            # request.auth is the Token instance for TokenAuthentication
            if hasattr(request.user, "auth_token"):
                request.user.auth_token.delete()
        except (AttributeError, Exception):
            # Handle cases where user doesn't have a token or uses different auth method
            # We still want to clear the session, so we don't raise an error
            pass

        # Clear Django session (for hybrid browser/API access)
        logout(request)

        return Response({"detail": "Pomyślnie wylogowano."}, status=status.HTTP_200_OK)


# -----------------------------------------------------------------------------
# Rating Views
# -----------------------------------------------------------------------------


class RatingAPIView(APIView):
    """
    API endpoint for creating or updating user ratings for routes or place descriptions.

    Implements UPSERT logic: creates a new rating or updates existing one for the same user/target combination.

    **Endpoint:** POST /api/ratings/

    **Request Body:**
    ```json
    {
        "rating_type": "route",
        "rating_value": 1,
        "route": 101,
        "place_description": null
    }
    ```

    **Success Response (201 Created - new rating):**
    ```json
    {
        "id": 42,
        "rating_type": "route",
        "rating_value": 1,
        "route": 101,
        "place_description": null
    }
    ```

    **Success Response (200 OK - updated rating):**
    ```json
    {
        "id": 42,
        "rating_type": "route",
        "rating_value": -1,
        "route": 101,
        "place_description": null
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "rating_value": ["Rating must be 1 (like) or -1 (dislike)."],
        "route": ["Route ID is required for route rating."]
    }
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - User is automatically set from authenticated request
    - UPSERT prevents duplicate ratings per user/target
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Handles POST requests for creating or updating ratings.

        Uses UPSERT logic via update_or_create to ensure one rating per user/target.

        Args:
            request: HTTP request object with rating data

        Returns:
            Response: JSON response with rating data and appropriate status code
                     - 201 Created if new rating was created
                     - 200 OK if existing rating was updated
                     - 400 Bad Request for validation errors
        """
        serializer = self.serializer_class(data=request.data)

        # Validate input data
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        rating_type = validated_data.get("rating_type")
        rating_value = validated_data.get("rating_value")
        route = validated_data.get("route")
        place_description = validated_data.get("place_description")

        # Determine lookup parameters based on rating_type
        lookup_params = {"user": request.user}

        if rating_type == "route":
            lookup_params["route"] = route
        elif rating_type == "place_description":
            lookup_params["place_description"] = place_description

        # UPSERT logic: create new rating or update existing one
        rating_instance, created = Rating.objects.update_or_create(
            **lookup_params,
            defaults={
                "rating_type": rating_type,
                "rating_value": rating_value,
                "route": route if rating_type == "route" else None,
                "place_description": place_description
                if rating_type == "place_description"
                else None,
            },
        )

        # Serialize the result
        response_serializer = self.serializer_class(rating_instance)

        # Return appropriate status code based on whether rating was created or updated
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(response_serializer.data, status=response_status)


# -----------------------------------------------------------------------------
# Route Views
# -----------------------------------------------------------------------------


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination configuration for list endpoints.

    Provides consistent pagination across the API with:
    - 10 items per page by default
    - Customizable page size via 'page_size' query parameter (max 100)
    - Clear next/previous links in response
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class RouteListAPIView(generics.ListCreateAPIView):
    """
    API endpoint for retrieving a paginated list of user's routes and creating new routes.

    Supports two operations:
    1. GET - List user's routes with filtering and pagination
    2. POST - Create new route (AI-generated or manual)

    **Endpoint:** GET /api/routes/
    **Endpoint:** POST /api/routes/

    **Required Headers:**
    - Authorization: Token <token_key>

    **GET Query Parameters:**
    - page: int - Page number for pagination (default: 1)
    - page_size: int - Number of items per page (default: 10, max: 100)
    - status: str - Filter by route status ('temporary', 'saved', default: 'saved')
    - ordering: str - Field to order by (supports: 'created_at', '-created_at', 'name', '-name',
                     'status', '-status', 'route_type', '-route_type', 'points_count', '-points_count')
                     Prefix with '-' for descending order (default: '-created_at')

    **GET Success Response (200 OK):**
    ```json
    {
        "count": 15,
        "next": "http://api.example.com/api/routes/?page=2",
        "previous": null,
        "results": [
            {
                "id": 101,
                "name": "Warsaw Old Town",
                "status": "saved",
                "route_type": "ai_generated",
                "created_at": "2024-01-01T12:00:00Z",
                "points_count": 5
            },
            ...
        ]
    }
    ```

    **POST Request Body (AI Generated):**
    ```json
    {
        "route_type": "ai_generated",
        "tags": [1, 5],
        "description": "Interesuje mnie architektura modernistyczna."
    }
    ```

    **POST Request Body (Manual):**
    ```json
    {
        "route_type": "manual",
        "name": "Wycieczka do Krakowa"
    }
    ```

    **POST Success Response (201 Created):**
    ```json
    {
        "id": 102,
        "name": "Modernist Architecture Tour",
        "status": "temporary",
        "route_type": "ai_generated",
        "user_rating_value": null,
        "points": [
            {
                "id": 505,
                "order": 0,
                "place": {
                    "id": 200,
                    "name": "Palace of Culture",
                    "lat": 52.23,
                    "lon": 21.01,
                    "address": "plac Defilad 1"
                },
                "description": {
                    "id": 901,
                    "content": "A notable landmark..."
                }
            }
        ]
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "tags": ["Tagi są wymagane dla tras generowanych przez AI."]
    }
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Automatic user isolation - users only see their own routes
    - Query parameter validation to prevent SQL injection
    - Rate limiting recommended for AI generation (10/hour)

    **Performance Optimizations:**
    - Uses annotated points_count to avoid N+1 queries
    - Leverages database indexes on (user, status, created_at)
    - Pagination limits data transfer and processing
    - AI generation is synchronous in MVP (will be async in future)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on request method.
        
        Returns:
            RouteCreateSerializer for POST requests
            RouteListSerializer for GET requests
        """
        if self.request.method == 'POST':
            return RouteCreateSerializer
        return RouteListSerializer

    def get_queryset(self) -> Any:
        """
        Retrieve the filtered queryset of routes for the authenticated user.

        Extracts query parameters (status, ordering) and delegates business logic
        to the route_list_selector for clean separation of concerns.

        Returns:
            QuerySet[Route]: Filtered and annotated queryset of routes

        Notes:
            - User is automatically extracted from request.user (authenticated)
            - Invalid query parameters are handled gracefully with defaults
        """
        user = self.request.user

        # Extract query parameters
        status_filter = self.request.query_params.get("status", None)
        ordering = self.request.query_params.get("ordering", None)

        # Delegate business logic to selector
        return route_list_selector(
            user=user,
            status_filter=status_filter,
            ordering=ordering,
        )

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Handle POST requests to create a new route.
        
        Validates input data, delegates to RouteService for business logic,
        and returns the created route with full details.
        
        Args:
            request: HTTP request with route data
            
        Returns:
            Response with created route data (201 Created)
            
        Raises:
            ValidationError: If input data is invalid (400 Bad Request)
            BusinessLogicException: If route creation fails (500 Internal Server Error)
        """
        # Validate input data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Delegate to service layer for route creation
            route = RouteService.create_route(
                user=request.user,
                validated_data=serializer.validated_data
            )
            
            logger.info(
                f"Route created successfully: route_id={route.id}, "
                f"user_id={request.user.id}, route_type={route.route_type}"
            )
            
            # Fetch the created route with all related data for response
            # Use the same queryset structure as RouteDetailAPIView
            route_with_details = Route.objects.filter(id=route.id).prefetch_related(
                Prefetch(
                    'points',
                    queryset=RoutePoint.objects.filter(is_removed=False)
                    .select_related('place')
                    .prefetch_related('description')
                    .order_by('position')
                )
            ).annotate(
                user_rating_value=Subquery(
                    Rating.objects.filter(
                        route=OuterRef('id'),
                        user=request.user,
                        rating_type=Rating.TYPE_ROUTE
                    ).values('rating_value')[:1],
                    output_field=IntegerField()
                )
            ).first()
            
            # Serialize the response
            response_serializer = RouteDetailSerializer(route_with_details)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except BusinessLogicException as e:
            logger.error(
                f"Business logic error during route creation: {str(e)}",
                exc_info=True
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during route creation: {str(e)}",
                exc_info=True
            )
            return Response(
                {"detail": "Wystąpił nieoczekiwany błąd. Spróbuj ponownie później."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RouteDetailAPIView(APIView):
    """
    API endpoint for retrieving, updating, and deleting a specific route.

    Provides operations on individual routes with automatic user isolation.

    **Endpoint:** GET /api/routes/{id}/
    **Endpoint:** PATCH /api/routes/{id}/
    **Endpoint:** DELETE /api/routes/{id}/

    **Required Headers:**
    - Authorization: Token <token_key>

    **Path Parameters:**
    - id: int - Unique identifier of the route

    **GET Success Response (200 OK):**
    ```json
    {
        "id": 101,
        "name": "Warsaw Old Town",
        "status": "temporary",
        "route_type": "ai_generated",
        "user_rating_value": 1,
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

    **PATCH Request Body (JSON, all fields optional):**
    ```json
    {
        "name": "My Trip to Paris",
        "status": "saved"
    }
    ```

    **PATCH Success Response (200 OK):**
    ```json
    {
        "id": 101,
        "name": "My Trip to Paris",
        "status": "saved",
        "route_type": "ai_generated",
        "saved_at": "2026-01-24T10:30:00Z",
        "created_at": "2026-01-24T10:00:00Z",
        "updated_at": "2026-01-24T10:30:00Z"
    }
    ```

    **DELETE Success Response (204 No Content):**
    Empty response body

    **Error Response (400 Bad Request):**
    ```json
    {
        "name": ["Nazwa trasy nie może być pusta."],
        "status": ["Nieprawidłowy status. Dozwolone wartości: 'temporary', 'saved'."]
    }
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Nie znaleziono."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Automatic user isolation - users can only access their own routes
    - Returns 404 for non-existent routes or routes belonging to other users
    - Atomic transaction ensures data consistency during updates and cascade deletion

    **Performance Optimizations (GET):**
    - Uses prefetch_related to avoid N+1 queries
    - Annotates user_rating_value using Subquery for efficiency
    - Points are ordered by position in the database

    **Business Logic (PATCH):**
    - When status changes from 'temporary' to 'saved', saved_at timestamp is automatically set
    - Both name and status are optional (partial update)
    - Name is trimmed and validated for length
    - Status must be one of: 'temporary', 'saved'

    **Cascade Deletion:**
    When a route is deleted, the following related objects are automatically removed:
    - RoutePoint (all points in the route)
    - PlaceDescription (descriptions for each point)
    - Rating (ratings for the route)
    - AIGenerationLog (AI generation logs)
    - RouteTag (tag associations)

    Note: Place objects remain in the database as they may be referenced by other routes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Any, pk: int, *args: Any, **kwargs: Any) -> Response:
        """
        Handles GET requests for retrieving route details.

        Retrieves a single route with all its points, places, and descriptions.
        Includes user's rating for the route if it exists.

        Args:
            request: HTTP request object with authenticated user
            pk: Primary key (ID) of the route to retrieve

        Returns:
            Response: JSON response with route details and 200 OK status
                     404 Not Found if route doesn't exist or belongs to another user
        """
        # Build optimized queryset with prefetch_related to avoid N+1 queries
        # Prefetch route points ordered by position, with related place and description
        route_points_prefetch = Prefetch(
            "points",
            queryset=RoutePoint.objects.select_related(
                "place", "description"
            ).order_by("position"),
        )

        # Subquery to get user's rating value for this route
        user_rating_subquery = Rating.objects.filter(
            route=OuterRef("pk"),
            user=request.user,
            rating_type=Rating.TYPE_ROUTE,
        ).values("rating_value")[:1]

        # Get route with all optimizations
        queryset = (
            Route.objects.filter(user=request.user)
            .prefetch_related(route_points_prefetch)
            .annotate(
                user_rating_value=Subquery(
                    user_rating_subquery, output_field=IntegerField()
                )
            )
        )

        # Get the route or return 404
        route = get_object_or_404(queryset, pk=pk)

        # Serialize and return
        serializer = RouteDetailSerializer(route)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request: Any, pk: int, *args: Any, **kwargs: Any) -> Response:
        """
        Handles PATCH requests for updating route name and/or status.

        Supports partial updates - all fields are optional.
        When status changes to 'saved', automatically sets saved_at timestamp.

        Args:
            request: HTTP request object with authenticated user and update data
            pk: Primary key (ID) of the route to update

        Returns:
            Response: JSON response with updated route data and 200 OK status
                     400 Bad Request for validation errors
                     404 Not Found if route doesn't exist or belongs to another user
        """
        # Get route belonging to the authenticated user
        # This ensures user isolation - returns 404 if route doesn't exist
        # or belongs to another user (security best practice)
        route = get_object_or_404(Route, pk=pk, user=request.user)

        # Validate input data
        serializer = RouteUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update route using service layer
        try:
            updated_route = RouteService.update_route(route, serializer.validated_data)
            
            # Prepare response with basic route information
            response_data = {
                "id": updated_route.id,
                "name": updated_route.name,
                "status": updated_route.status,
                "route_type": updated_route.route_type,
                "saved_at": updated_route.saved_at,
                "created_at": updated_route.created_at,
                "updated_at": updated_route.updated_at,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unexpected error during route update: "
                f"route_id={pk}, user_id={request.user.id}, error={str(e)}",
                exc_info=True
            )
            return Response(
                {"detail": "Wystąpił błąd podczas aktualizacji trasy."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def delete(self, request: Any, pk: int, *args: Any, **kwargs: Any) -> Response:
        """
        Handles DELETE requests for removing a route.

        Ensures the route belongs to the authenticated user before deletion.
        Uses atomic transaction to ensure all related objects are deleted consistently.

        Args:
            request: HTTP request object with authenticated user
            pk: Primary key (ID) of the route to delete

        Returns:
            Response: Empty response with 204 No Content status on success
                     404 Not Found if route doesn't exist or belongs to another user
        """
        # Get route belonging to the authenticated user
        # This ensures user isolation - returns 404 if route doesn't exist
        # or belongs to another user (security best practice)
        route = get_object_or_404(Route, pk=pk, user=request.user)

        # Delete the route
        # Cascade deletion of related objects is handled by database constraints:
        # - route_points (ON DELETE CASCADE)
        # - place_descriptions (via route_points, ON DELETE CASCADE)
        # - ratings (ON DELETE CASCADE)
        # - ai_generation_logs (ON DELETE CASCADE)
        # - route_tags (ON DELETE CASCADE)
        route.delete()

        # Return 204 No Content (standard response for successful DELETE)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RouteOptimizeAPIView(APIView):
    """
    API endpoint for optimizing the order of points in a manual route.

    Applies optimization algorithm (e.g., nearest neighbor TSP) to find the shortest
    path between all points in the route. Updates point positions permanently.

    **Endpoint:** POST /api/routes/{id}/optimize/

    **Required Headers:**
    - Authorization: Token <token_key>

    **Path Parameters:**
    - id: int - Unique identifier of the route

    **Request Body (JSON, optional):**
    ```json
    {
        "strategy": "nearest_neighbor"
    }
    ```

    **Success Response (200 OK):**
    ```json
    [
        {
            "id": 501,
            "order": 0,
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
        },
        {
            "id": 502,
            "order": 1,
            "place": { ... },
            "description": { ... }
        }
    ]
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "detail": "Tylko trasy typu 'manual' mogą być optymalizowane."
    }
    ```
    or
    ```json
    {
        "detail": "Trasa musi mieć co najmniej 2 punkty, aby można było ją optymalizować."
    }
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Nie znaleziono."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Automatic user isolation - users can only optimize their own routes
    - Returns 404 for non-existent routes or routes belonging to other users
    - Atomic transaction ensures data consistency during position updates

    **Business Rules:**
    - Only manual routes can be optimized (ai_generated routes are read-only)
    - Route must have at least 2 points to optimize
    - First point is kept as starting location, rest are optimized

    **Performance:**
    - Uses bulk_update for efficient database operations
    - Transaction atomic ensures consistency
    - Suitable for routes with up to ~50 points (O(n²) complexity)
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Any, pk: int, *args: Any, **kwargs: Any) -> Response:
        """
        Handles POST requests for route optimization.

        Validates input parameters, checks business rules, applies optimization
        algorithm, and returns the updated list of points.

        Args:
            request: HTTP request object with authenticated user and optional config
            pk: Primary key (ID) of the route to optimize

        Returns:
            Response: JSON response with optimized points list and 200 OK status
                     400 Bad Request if business rules are violated
                     404 Not Found if route doesn't exist or belongs to another user
        """
        # Validate input serializer
        input_serializer = RouteOptimizeInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get validated configuration
        config = input_serializer.validated_data

        # Get route belonging to the authenticated user
        # This ensures user isolation - returns 404 if route doesn't exist
        # or belongs to another user (security best practice)
        route = get_object_or_404(Route, pk=pk, user=request.user)

        try:
            # Call service layer to perform optimization
            optimized_points = RouteService.optimize_route(route, config)

            # Reload points with related data for serialization
            # We need to refetch to get the updated positions and include descriptions
            route_points_with_relations = (
                RoutePoint.objects.filter(route=route, is_removed=False)
                .select_related('place', 'description')
                .order_by('position')
            )

            # Serialize and return optimized points
            serializer = RoutePointDetailSerializer(
                route_points_with_relations,
                many=True
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        except BusinessLogicException as e:
            # Business rule violation (wrong route type, too few points)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Unexpected error - log and return 500
            logger.error(
                f"Unexpected error during route optimization: "
                f"route_id={pk}, user_id={request.user.id}, error={str(e)}",
                exc_info=True
            )
            return Response(
                {"detail": "Wystąpił błąd podczas optymalizacji trasy."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RouteAddPointAPIView(APIView):
    """
    API endpoint for adding a new point (place) to an existing manual route.

    Automatically handles Place creation if it doesn't exist (lookup by osm_id or wikipedia_id).
    Only manual routes can have points added - AI generated routes are read-only.

    **Endpoint:** POST /api/routes/{id}/points/

    **Required Headers:**
    - Authorization: Token <token_key>

    **Path Parameters:**
    - id: int - Unique identifier of the route

    **Request Body (JSON):**
    ```json
    {
        "place": {
            "name": "Palace of Culture",
            "lat": 52.231,
            "lon": 21.006,
            "osm_id": 123456,
            "address": "Plac Defilad 1",
            "wikipedia_id": "pl:Pałac Kultury i Nauki"
        }
    }
    ```

    **Required Fields:**
    - place.name: string - Name of the place
    - place.lat: float - Latitude (-90 to 90)
    - place.lon: float - Longitude (-180 to 180)

    **Optional Fields:**
    - place.osm_id: int - OpenStreetMap ID (used for deduplication)
    - place.address: string - Full address
    - place.wikipedia_id: string - Wikipedia identifier

    **Success Response (201 Created):**
    ```json
    {
        "id": 101,
        "position": 5,
        "place": {
            "id": 55,
            "name": "Palace of Culture",
            "osm_id": 123456,
            "wikipedia_id": "pl:Pałac Kultury i Nauki",
            "address": "Plac Defilad 1",
            "city": null,
            "country": null,
            "lat": 52.231,
            "lon": 21.006,
            "data": {}
        },
        "description": null
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "detail": "Cannot add points to AI generated route."
    }
    ```
    or
    ```json
    {
        "detail": "Max points limit reached."
    }
    ```
    or
    ```json
    {
        "place": {
            "name": ["To pole jest wymagane."],
            "lat": ["Upewnij się, że ta wartość jest większa lub równa -90."]
        }
    }
    ```

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Nie znaleziono."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Automatic user isolation - users can only modify their own routes
    - Returns 404 for non-existent routes or routes belonging to other users
    - Atomic transaction ensures data consistency

    **Business Rules:**
    - Only manual routes can have points added (ai_generated routes are read-only)
    - Maximum 10 points per manual route (enforced by database trigger)
    - Place deduplication by osm_id or wikipedia_id
    - Automatic position calculation (appends to end of route)

    **Performance:**
    - Efficient Place lookup using indexed fields (osm_id, wikipedia_id)
    - Single database transaction for consistency
    - Minimal queries with select_related for response serialization
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Any, pk: int, *args: Any, **kwargs: Any) -> Response:
        """
        Handles POST requests for adding a point to a route.

        Validates input data, checks business rules (route type, point limit),
        creates or finds the Place, and adds it to the route.

        Args:
            request: HTTP request object with authenticated user and place data
            pk: Primary key (ID) of the route to add point to

        Returns:
            Response: JSON response with created RoutePoint data and 201 Created status
                     400 Bad Request if business rules are violated or validation fails
                     404 Not Found if route doesn't exist or belongs to another user
        """
        # Get route belonging to the authenticated user
        # This ensures user isolation - returns 404 if route doesn't exist
        # or belongs to another user (security best practice)
        route = get_object_or_404(Route, pk=pk, user=request.user)

        # Initialize serializer with route context for validation
        serializer = RoutePointCreateSerializer(
            data=request.data,
            context={'route': route, 'request': request}
        )

        # Validate input data and business rules
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create the route point (handles Place lookup/creation internally)
            route_point = serializer.save()

            # Reload with related data for response serialization
            route_point_with_relations = (
                RoutePoint.objects
                .select_related('place', 'description')
                .get(pk=route_point.pk)
            )

            # Serialize and return the created point
            response_serializer = RoutePointSerializer(route_point_with_relations)

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unexpected error during route point creation: "
                f"route_id={pk}, user_id={request.user.id}, error={str(e)}",
                exc_info=True
            )
            return Response(
                {"detail": "Wystąpił błąd podczas dodawania punktu do trasy."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoutePointDeleteAPIView(APIView):
    """
    API endpoint for removing a specific point from a route (soft delete).

    Marks a route point as removed by setting the is_removed flag to True.
    This preserves the associated PlaceDescription and AI-generated content
    while hiding the point from route queries.

    **Endpoint:** DELETE /api/routes/{id}/points/{point_id}/

    **Required Headers:**
    - Authorization: Token <token_key>

    **Path Parameters:**
    - id: int - Unique identifier of the route
    - point_id: int - Unique identifier of the route point to remove

    **Request Body:** Empty

    **Success Response (204 No Content):**
    Empty response body

    **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Nie podano danych uwierzytelniających."
    }
    ```

    **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Nie znaleziono."
    }
    ```

    **Security Features:**
    - Requires authentication (IsAuthenticated permission)
    - Automatic user isolation - users can only remove points from their own routes
    - Returns 404 for non-existent points or points belonging to other users' routes
    - Atomic transaction ensures data consistency

    **Business Logic:**
    - Implements soft delete (sets is_removed = True)
    - Preserves PlaceDescription and AI-generated content
    - Does not modify point positions
    - Idempotent - can be called multiple times safely

    **Performance:**
    - Single database update operation
    - Efficient indexed query on route_id and point_id
    """

    permission_classes = [IsAuthenticated, IsRouteOwner]

    @transaction.atomic
    def delete(self, request: Any, pk: int, point_id: int, *args: Any, **kwargs: Any) -> Response:
        """
        Handles DELETE requests for removing a route point (soft delete).

        Validates that the point exists and belongs to the specified route,
        checks user ownership, and marks the point as removed.

        Args:
            request: HTTP request object with authenticated user
            pk: Primary key (ID) of the route
            point_id: Primary key (ID) of the route point to remove

        Returns:
            Response: Empty response with 204 No Content status on success
                     404 Not Found if route or point doesn't exist or belongs to another user
        """
        # Get the route belonging to the authenticated user
        # This ensures user isolation - returns 404 if route doesn't exist
        # or belongs to another user (security best practice)
        route = get_object_or_404(Route, pk=pk, user=request.user)

        # Get the route point belonging to this specific route
        # This ensures that the point_id actually belongs to the route_id
        # preventing logical errors where a user might try to delete a point
        # from a different route
        route_point = get_object_or_404(
            RoutePoint,
            pk=point_id,
            route=route
        )

        # Check object-level permission (IsRouteOwner)
        # This is redundant since we already filtered by user, but it's
        # good practice for consistency with DRF permission system
        self.check_object_permissions(request, route_point)

        try:
            # Perform soft delete via service layer
            RouteService.soft_delete_point(route_point)

            logger.info(
                f"Route point soft deleted: point_id={point_id}, "
                f"route_id={pk}, user_id={request.user.id}"
            )

            # Return 204 No Content (standard response for successful DELETE)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error during route point deletion: "
                f"point_id={point_id}, route_id={pk}, user_id={request.user.id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return Response(
                {"detail": "Wystąpił błąd podczas usuwania punktu z trasy."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
