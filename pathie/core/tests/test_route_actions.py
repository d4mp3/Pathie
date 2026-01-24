from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from ..models import Route, RoutePoint, Place, Rating

User = get_user_model()


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

    def test_delete_route_allowed_methods(self):
        """Test that GET, PATCH, and DELETE methods are allowed for route detail endpoint."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route1.id}/"

        # GET method should work (returns route details)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # PATCH method should work (updates route)
        response = self.client.patch(url, {"name": "Updated via PATCH"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try POST method - should fail
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT method - should fail
        response = self.client.put(url, {})
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


class RoutePatchAPIViewTests(TestCase):
    """
    Test suite for route PATCH endpoint.
    Tests PATCH /api/routes/{id}/ endpoint functionality for updating routes.
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
        self.temp_route = Route.objects.create(
            user=self.user1,
            name="Temporary Route",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_AI_GENERATED,
        )
        self.saved_route = Route.objects.create(
            user=self.user1,
            name="Saved Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_MANUAL,
        )

        # Create test route for user2
        self.user2_route = Route.objects.create(
            user=self.user2,
            name="User 2 Route",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_MANUAL,
        )

    def test_patch_route_update_name_success(self):
        """Test successful update of route name."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Update name
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "Updated Route Name"}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Route Name")
        self.assertEqual(response.data["status"], Route.STATUS_TEMPORARY)
        self.assertIsNone(response.data["saved_at"])

        # Verify database was updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Updated Route Name")

    def test_patch_route_update_status_success(self):
        """Test successful update of route status to saved."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Update status to saved
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"status": Route.STATUS_SAVED}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Route.STATUS_SAVED)
        self.assertIsNotNone(response.data["saved_at"])

        # Verify database was updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.status, Route.STATUS_SAVED)
        self.assertIsNotNone(self.temp_route.saved_at)

    def test_patch_route_update_name_and_status_success(self):
        """Test successful update of both name and status."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Update both fields
        url = f"/api/routes/{self.temp_route.id}/"
        data = {
            "name": "My Trip to Paris",
            "status": Route.STATUS_SAVED,
        }
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "My Trip to Paris")
        self.assertEqual(response.data["status"], Route.STATUS_SAVED)
        self.assertIsNotNone(response.data["saved_at"])

        # Verify database was updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "My Trip to Paris")
        self.assertEqual(self.temp_route.status, Route.STATUS_SAVED)

    def test_patch_route_unauthorized(self):
        """Test PATCH without authentication returns 401."""
        # No authentication
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "Unauthorized Update"}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify route was not updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Temporary Route")

    def test_patch_route_other_user_returns_404(self):
        """Test user cannot update another user's route (returns 404)."""
        # Authenticate as user2
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")

        # Try to update user1's route
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "Hacked Name"}
        response = self.client.patch(url, data, format="json")

        # Verify response (404 for security - don't reveal existence)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify route was not updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Temporary Route")

    def test_patch_route_invalid_status(self):
        """Test PATCH with invalid status returns 400."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to update with invalid status
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"status": "invalid_status"}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

        # Verify route was not updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.status, Route.STATUS_TEMPORARY)

    def test_patch_route_empty_name(self):
        """Test PATCH with empty name returns 400."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to update with empty name
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": ""}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

        # Verify route was not updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Temporary Route")

    def test_patch_route_name_too_long(self):
        """Test PATCH with name exceeding 500 characters returns 400."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to update with very long name
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "A" * 501}  # 501 characters
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

        # Verify route was not updated
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Temporary Route")

    def test_patch_route_whitespace_only_name(self):
        """Test PATCH with whitespace-only name returns 400."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to update with whitespace-only name
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "   "}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_patch_route_not_found(self):
        """Test PATCH with non-existent route ID returns 404."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to update non-existent route
        url = "/api/routes/99999/"
        data = {"name": "Non-existent"}
        response = self.client.patch(url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_route_response_contains_all_fields(self):
        """Test that PATCH response contains all expected fields."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Update route
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "Complete Response Test"}
        response = self.client.patch(url, data, format="json")

        # Verify response contains all expected fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = {
            "id",
            "name",
            "status",
            "route_type",
            "saved_at",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_patch_route_partial_update_allowed(self):
        """Test that PATCH allows partial updates (not all fields required)."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Update only name (status not provided)
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "Partial Update"}
        response = self.client.patch(url, data, format="json")

        # Verify success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Partial Update")
        self.assertEqual(response.data["status"], Route.STATUS_TEMPORARY)

    def test_patch_route_name_trimmed(self):
        """Test that route name is automatically trimmed of whitespace."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Update with name that has leading/trailing whitespace
        url = f"/api/routes/{self.temp_route.id}/"
        data = {"name": "  Trimmed Name  "}
        response = self.client.patch(url, data, format="json")

        # Verify response has trimmed name
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Trimmed Name")

        # Verify database has trimmed name
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Trimmed Name")
