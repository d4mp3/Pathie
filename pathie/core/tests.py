from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import Route, RoutePoint, Place, Rating

User = get_user_model()


# -----------------------------------------------------------------------------
# Authentication Tests
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Route Delete Tests
# -----------------------------------------------------------------------------


class RouteDeleteAPIViewTests(TestCase):
    """
    Test suite for route deletion endpoint.
    Tests DELETE /api/routes/{id}/ endpoint functionality.
    """

    def setUp(self):
        """Set up test client, users, and test routes."""
        self.client = APIClient()

        # Create two test users
        self.user1 = User.objects.create_user(
            username="user1@example.com",
            email="user1@example.com",
            password="testpass123",
            is_active=True,
        )
        self.user2 = User.objects.create_user(
            username="user2@example.com",
            email="user2@example.com",
            password="testpass123",
            is_active=True,
        )

        # Create tokens for authentication
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Create test routes for user1
        self.route1 = Route.objects.create(
            user=self.user1,
            name="User 1 Route 1",
            status="saved",
            route_type="manual",
        )
        self.route2 = Route.objects.create(
            user=self.user1,
            name="User 1 Route 2",
            status="temporary",
            route_type="ai_generated",
        )

        # Create test route for user2
        self.route3 = Route.objects.create(
            user=self.user2,
            name="User 2 Route 1",
            status="saved",
            route_type="manual",
        )

        # Create a place for testing cascade deletion
        self.place = Place.objects.create(
            name="Test Place",
            lat=52.2297,
            lon=21.0122,
            osm_id=123456,
        )

        # Add route points to route1
        self.route_point1 = RoutePoint.objects.create(
            route=self.route1,
            place=self.place,
            position=1,
            source="manual",
        )
        self.route_point2 = RoutePoint.objects.create(
            route=self.route1,
            place=self.place,
            position=2,
            source="manual",
        )

        # Add rating to route1
        self.rating = Rating.objects.create(
            user=self.user1,
            rating_type="route",
            rating_value=1,
            route=self.route1,
        )

    def test_delete_route_success(self):
        """Test successful deletion of own route returns 204."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Get initial counts
        initial_route_count = Route.objects.count()
        initial_point_count = RoutePoint.objects.count()
        initial_rating_count = Rating.objects.count()

        # Delete route1
        url = f"/api/routes/{self.route1.id}/"
        response = self.client.delete(url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, None)

        # Verify route was deleted
        self.assertEqual(Route.objects.count(), initial_route_count - 1)
        self.assertFalse(Route.objects.filter(id=self.route1.id).exists())

        # Verify cascade deletion of route points
        self.assertEqual(RoutePoint.objects.count(), initial_point_count - 2)
        self.assertFalse(RoutePoint.objects.filter(route=self.route1).exists())

        # Verify cascade deletion of ratings
        self.assertEqual(Rating.objects.count(), initial_rating_count - 1)
        self.assertFalse(Rating.objects.filter(route=self.route1).exists())

        # Verify place still exists (should not be deleted)
        self.assertTrue(Place.objects.filter(id=self.place.id).exists())

    def test_delete_route_not_found(self):
        """Test deletion of non-existent route returns 404."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to delete non-existent route
        url = "/api/routes/99999/"
        response = self.client.delete(url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_route_unauthorized(self):
        """Test deletion without authentication returns 401."""
        # No authentication
        url = f"/api/routes/{self.route1.id}/"
        response = self.client.delete(url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify route was not deleted
        self.assertTrue(Route.objects.filter(id=self.route1.id).exists())

    def test_delete_route_other_user(self):
        """Test user cannot delete another user's route (returns 404)."""
        # Authenticate as user2
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")

        # Try to delete user1's route
        url = f"/api/routes/{self.route1.id}/"
        response = self.client.delete(url)

        # Verify response (404 instead of 403 for security - don't reveal existence)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify route was not deleted
        self.assertTrue(Route.objects.filter(id=self.route1.id).exists())

    def test_delete_route_invalid_token(self):
        """Test deletion with invalid token returns 401."""
        # Use invalid token
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken123")

        url = f"/api/routes/{self.route1.id}/"
        response = self.client.delete(url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify route was not deleted
        self.assertTrue(Route.objects.filter(id=self.route1.id).exists())

    def test_delete_route_only_delete_method_allowed(self):
        """Test that only DELETE method works for deletion endpoint."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route1.id}/"

        # Try GET method
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try POST method
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT method
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PATCH method
        response = self.client.patch(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Verify route still exists
        self.assertTrue(Route.objects.filter(id=self.route1.id).exists())

    def test_delete_route_cascade_multiple_points(self):
        """Test that deleting route with multiple points removes all of them."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Verify initial state
        self.assertEqual(RoutePoint.objects.filter(route=self.route1).count(), 2)

        # Delete route
        url = f"/api/routes/{self.route1.id}/"
        response = self.client.delete(url)

        # Verify success
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify all points were deleted
        self.assertEqual(RoutePoint.objects.filter(route=self.route1).count(), 0)

    def test_delete_route_without_points(self):
        """Test deletion of route without any points."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Delete route2 (has no points)
        url = f"/api/routes/{self.route2.id}/"
        response = self.client.delete(url)

        # Verify success
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Route.objects.filter(id=self.route2.id).exists())
