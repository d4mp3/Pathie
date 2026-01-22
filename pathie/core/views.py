from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import get_user_model, logout
from typing import Any

from .serializers import LoginSerializer

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

        return Response(
            {"detail": "Pomyślnie wylogowano."}, status=status.HTTP_200_OK
        )
