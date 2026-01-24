from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from ..models import Route, RoutePoint, Place, PlaceDescription

User = get_user_model()


class RoutePointDeleteAPIViewTests(TestCase):
    """
    Test suite for route point deletion endpoint (soft delete).
    Tests DELETE /api/routes/{id}/points/{point_id}/
    """

    def setUp(self):
        """Set up test client, users, routes, and route points."""
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username="user1@example.com",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2@example.com",
            email="user2@example.com",
            password="testpass123",
        )

        # Create authentication tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Create test places
        self.place1 = Place.objects.create(
            name="Test Place 1",
            lat=52.2297,
            lon=21.0122,
            osm_id=1001,
        )
        self.place2 = Place.objects.create(
            name="Test Place 2",
            lat=52.2319,
            lon=21.0067,
            osm_id=1002,
        )
        self.place3 = Place.objects.create(
            name="Test Place 3",
            lat=52.2400,
            lon=21.0100,
            osm_id=1003,
        )

        # Create route for user1
        self.route_user1 = Route.objects.create(
            user=self.user1,
            name="User1 Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_MANUAL,
        )

        # Create route for user2
        self.route_user2 = Route.objects.create(
            user=self.user2,
            name="User2 Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_MANUAL,
        )

        # Create route points for user1's route
        self.point1_user1 = RoutePoint.objects.create(
            route=self.route_user1,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
            is_removed=False,
        )
        self.point2_user1 = RoutePoint.objects.create(
            route=self.route_user1,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
            is_removed=False,
        )

        # Create route point for user2's route
        self.point1_user2 = RoutePoint.objects.create(
            route=self.route_user2,
            place=self.place3,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
            is_removed=False,
        )

        # Create place description for point1_user1 (to verify it's preserved)
        # Note: content must be between 2500-5000 characters per database constraint
        long_content = (
            "AI generated description for place 1. " * 100
        )  # ~3900 characters
        self.description1 = PlaceDescription.objects.create(
            route_point=self.point1_user1,
            content=long_content,
            language_code="pl",
        )

    def test_delete_own_point_success(self):
        """Test user successfully deletes their own route point (soft delete)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"
        response = self.client.delete(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)  # Empty response body

        # Verify soft delete - point still exists but is_removed=True
        self.point1_user1.refresh_from_db()
        self.assertTrue(self.point1_user1.is_removed)

        # Verify other fields unchanged
        self.assertEqual(self.point1_user1.position, 0)
        self.assertEqual(self.point1_user1.place, self.place1)
        self.assertEqual(self.point1_user1.route, self.route_user1)

    def test_delete_point_preserves_description(self):
        """Test that soft delete preserves the PlaceDescription (AI content)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify PlaceDescription still exists
        self.assertTrue(
            PlaceDescription.objects.filter(id=self.description1.id).exists()
        )

        # Verify description is still linked to the route point
        self.description1.refresh_from_db()
        self.assertEqual(self.description1.route_point, self.point1_user1)
        # Verify content is preserved (starts with expected text)
        self.assertTrue(
            self.description1.content.startswith("AI generated description for place 1")
        )

    def test_delete_other_user_point_returns_404(self):
        """Test user cannot delete another user's route point."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to delete user2's point
        url = f"/api/routes/{self.route_user2.id}/points/{self.point1_user2.id}/"
        response = self.client.delete(url)

        # Should return 404 (not found) for security reasons
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify point was NOT deleted
        self.point1_user2.refresh_from_db()
        self.assertFalse(self.point1_user2.is_removed)

    def test_delete_nonexistent_point_returns_404(self):
        """Test deleting non-existent route point returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Use non-existent point_id
        url = f"/api/routes/{self.route_user1.id}/points/99999/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_point_from_wrong_route_returns_404(self):
        """Test deleting a point with mismatched route_id returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Try to delete point1_user1 using wrong route_id
        # This tests the validation that point_id must belong to route_id
        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user2.id}/"
        response = self.client.delete(url)

        # Should return 404 because point1_user2 doesn't belong to route_user1
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify point was NOT deleted
        self.point1_user2.refresh_from_db()
        self.assertFalse(self.point1_user2.is_removed)

    def test_delete_without_authentication_returns_401(self):
        """Test deleting route point without authentication returns 401."""
        # Don't set credentials
        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify point was NOT deleted
        self.point1_user1.refresh_from_db()
        self.assertFalse(self.point1_user1.is_removed)

    def test_delete_idempotency(self):
        """Test that deleting the same point multiple times is idempotent (always returns 204)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"

        # First delete
        response1 = self.client.delete(url)
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete
        self.point1_user1.refresh_from_db()
        self.assertTrue(self.point1_user1.is_removed)

        # Second delete (should still return 204 for idempotency)
        response2 = self.client.delete(url)
        self.assertEqual(response2.status_code, status.HTTP_204_NO_CONTENT)

        # Third delete
        response3 = self.client.delete(url)
        self.assertEqual(response3.status_code, status.HTTP_204_NO_CONTENT)

        # Verify is_removed is still True
        self.point1_user1.refresh_from_db()
        self.assertTrue(self.point1_user1.is_removed)

    def test_delete_does_not_affect_other_points(self):
        """Test that deleting one point doesn't affect other points in the route."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify only point1 is removed
        self.point1_user1.refresh_from_db()
        self.assertTrue(self.point1_user1.is_removed)

        # Verify point2 is NOT removed
        self.point2_user1.refresh_from_db()
        self.assertFalse(self.point2_user1.is_removed)

    def test_delete_already_removed_point(self):
        """Test deleting a point that was already soft deleted returns 204."""
        # Pre-mark point as removed
        self.point1_user1.is_removed = True
        self.point1_user1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"
        response = self.client.delete(url)

        # Should still return 204 (idempotent operation)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify is_removed is still True
        self.point1_user1.refresh_from_db()
        self.assertTrue(self.point1_user1.is_removed)

    def test_delete_point_preserves_place(self):
        """Test that soft deleting a route point preserves the Place object."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        place_id = self.place1.id

        url = f"/api/routes/{self.route_user1.id}/points/{self.point1_user1.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify Place still exists in database
        self.assertTrue(Place.objects.filter(id=place_id).exists())

        # Verify Place data is unchanged
        place = Place.objects.get(id=place_id)
        self.assertEqual(place.name, "Test Place 1")
        self.assertEqual(place.lat, 52.2297)
        self.assertEqual(place.lon, 21.0122)
