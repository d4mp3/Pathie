from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import get_user_model, logout
from typing import Any

from .serializers import LoginSerializer, RatingSerializer
from .models import Rating

User = get_user_model()


# -----------------------------------------------------------------------------
# Authentication Views
# -----------------------------------------------------------------------------


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
