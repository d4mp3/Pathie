from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch

User = get_user_model()


class LoginAPIViewTests(TestCase):
    """
    Test suite for user login endpoint.
    """

    def setUp(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.login_url = "/api/auth/login/"
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            is_active=True,
        )

    def test_login_success(self):
        """Test successful login returns token."""
        response = self.client.post(
            self.login_url,
            {"email": "testuser@example.com", "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("key", response.data)
        self.assertEqual(len(response.data["key"]), 40)  # Token key length

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 400."""
        response = self.client.post(
            self.login_url,
            {"email": "testuser@example.com", "password": "wrongpassword"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_login_missing_email(self):
        """Test login without email returns 400."""
        response = self.client.post(
            self.login_url, {"password": "testpass123"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_missing_password(self):
        """Test login without password returns 400."""
        response = self.client.post(
            self.login_url, {"email": "testuser@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_inactive_user(self):
        """Test login with inactive user returns 400."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.login_url,
            {"email": "testuser@example.com", "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutAPIViewTests(TestCase):
    """
    Test suite for user logout endpoint.
    """

    def setUp(self):
        """Set up test client, test user, and authentication token."""
        self.client = APIClient()
        self.logout_url = "/api/auth/logout/"
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            is_active=True,
        )
        self.token = Token.objects.create(user=self.user)

    def test_logout_success(self):
        """Test successful logout deletes token and returns 200."""
        # Authenticate with token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Perform logout
        response = self.client.post(self.logout_url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Pomyślnie wylogowano.")

        # Verify token was deleted from database
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_logout_without_authentication(self):
        """Test logout without authentication returns 401."""
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_logout_with_invalid_token(self):
        """Test logout with invalid token returns 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken123")

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_token_cannot_be_reused(self):
        """Test that token cannot be used after logout."""
        # Authenticate with token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Perform logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try to use the same token again
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_only_post_method_allowed(self):
        """Test that only POST method is allowed for logout."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Try GET method
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT method
        response = self.client.put(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try DELETE method
        response = self.client.delete(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_logout_idempotency(self):
        """Test logout behavior when user has no token (edge case)."""
        # Delete token manually
        self.token.delete()

        # Create new token for authentication
        new_token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {new_token.key}")

        # Logout should still work
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@patch("core.views.RegistrationAPIView.throttle_classes", [])
class RegistrationAPIViewTests(TestCase):
    """
    Test suite for user registration endpoint.
    Tests POST /api/auth/registration/ endpoint functionality.
    """

    def setUp(self):
        """Set up test client and registration URL."""
        self.client = APIClient()
        self.registration_url = "/api/auth/registration/"

    def test_registration_success(self):
        """Test successful user registration returns token and user data."""
        data = {
            "email": "testuser@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertIn("user_id", response.data)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"], "testuser@example.com")
        self.assertEqual(len(response.data["token"]), 40)  # Token key length

        # Verify user was created in database
        user = User.objects.get(email="testuser@example.com")
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertTrue(user.is_active)

        # Verify token was created
        token = Token.objects.get(user=user)
        self.assertEqual(token.key, response.data["token"])

    def test_registration_email_already_exists(self):
        """Test registration with existing email returns 400."""
        # Create existing user
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="ExistingPass123!",
        )

        # Try to register with same email
        data = {
            "email": "existing@example.com",
            "password": "NewPass123!",
            "password_confirm": "NewPass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("już istnieje", response.data["email"][0])

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords returns 400."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass456!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)
        self.assertIn("nie są identyczne", response.data["password_confirm"][0])

        # Verify user was not created
        self.assertFalse(User.objects.filter(email="newuser@example.com").exists())

    def test_registration_weak_password_too_short(self):
        """Test registration with password too short returns 400."""
        data = {
            "email": "weakpass@example.com",
            "password": "short",
            "password_confirm": "short",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn("za krótkie", response.data["password"][0])

        # Verify user was not created
        self.assertFalse(User.objects.filter(email="weakpass@example.com").exists())

    def test_registration_common_password(self):
        """Test registration with common password returns 400."""
        data = {
            "email": "common@example.com",
            "password": "password123",
            "password_confirm": "password123",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn("powszechne", response.data["password"][0])

        # Verify user was not created
        self.assertFalse(User.objects.filter(email="common@example.com").exists())

    def test_registration_invalid_email_format(self):
        """Test registration with invalid email format returns 400."""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("prawidłowy adres e-mail", response.data["email"][0])

    def test_registration_missing_email(self):
        """Test registration without email returns 400."""
        data = {
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_missing_password(self):
        """Test registration without password returns 400."""
        data = {
            "email": "test@example.com",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_missing_password_confirm(self):
        """Test registration without password confirmation returns 400."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_registration_missing_all_fields(self):
        """Test registration without any fields returns 400."""
        data = {}

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)
        self.assertIn("password_confirm", response.data)

    def test_registration_email_normalization(self):
        """Test that email is normalized to lowercase."""
        data = {
            "email": "TestUser@EXAMPLE.COM",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "testuser@example.com")

        # Verify user was created with normalized email
        user = User.objects.get(email="testuser@example.com")
        self.assertEqual(user.email, "testuser@example.com")

    def test_registration_token_can_be_used_for_authentication(self):
        """Test that returned token can be used for authenticated requests."""
        # Register user
        data = {
            "email": "authtest@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post(self.registration_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token = response.data["token"]

        # Try to use token for authenticated request (logout)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        logout_response = self.client.post("/api/auth/logout/")
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

    def test_registration_only_post_method_allowed(self):
        """Test that only POST method is allowed for registration."""
        # Try GET method
        response = self.client.get(self.registration_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT method
        response = self.client.put(self.registration_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try DELETE method
        response = self.client.delete(self.registration_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
