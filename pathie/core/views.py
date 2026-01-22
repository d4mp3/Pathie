from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import get_user_model
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
