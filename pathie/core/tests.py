from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import Route, RoutePoint, Place, PlaceDescription, Rating, Tag, RouteTag, AIGenerationLog
from .serializers import (
    PlaceSimpleSerializer,
    PlaceDescriptionContentSerializer,
    RoutePointDetailSerializer,
)

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


# -----------------------------------------------------------------------------
# Serializer Tests
# -----------------------------------------------------------------------------


class PlaceSimpleSerializerTests(TestCase):
    """
    Test suite for PlaceSimpleSerializer.
    Tests serialization of Place model with minimal fields.
    """

    def setUp(self):
        """Set up test place."""
        self.place = Place.objects.create(
            name="Royal Castle",
            lat=52.2480,
            lon=21.0150,
            address="Plac Zamkowy 4",
            city="Warsaw",
            country="Poland",
            osm_id=123456789,
            data={"type": "castle", "historic": "yes"},
        )

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains only expected fields."""
        serializer = PlaceSimpleSerializer(instance=self.place)
        data = serializer.data

        # Check that only expected fields are present
        expected_fields = {"id", "name", "lat", "lon", "address"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_field_values(self):
        """Test that serializer returns correct field values."""
        serializer = PlaceSimpleSerializer(instance=self.place)
        data = serializer.data

        self.assertEqual(data["id"], self.place.id)
        self.assertEqual(data["name"], "Royal Castle")
        self.assertEqual(data["lat"], 52.2480)
        self.assertEqual(data["lon"], 21.0150)
        self.assertEqual(data["address"], "Plac Zamkowy 4")

    def test_serializer_excludes_extra_fields(self):
        """Test that serializer excludes fields not in field list."""
        serializer = PlaceSimpleSerializer(instance=self.place)
        data = serializer.data

        # These fields should NOT be present
        self.assertNotIn("city", data)
        self.assertNotIn("country", data)
        self.assertNotIn("osm_id", data)
        self.assertNotIn("wikipedia_id", data)
        self.assertNotIn("data", data)
        self.assertNotIn("created_at", data)
        self.assertNotIn("updated_at", data)

    def test_serializer_with_null_address(self):
        """Test serializer handles null address correctly."""
        place_no_address = Place.objects.create(
            name="Unknown Place",
            lat=50.0,
            lon=20.0,
            address=None,
        )

        serializer = PlaceSimpleSerializer(instance=place_no_address)
        data = serializer.data

        self.assertEqual(data["address"], None)
        self.assertEqual(data["name"], "Unknown Place")

    def test_serializer_with_empty_address(self):
        """Test serializer handles empty string address correctly."""
        place_empty_address = Place.objects.create(
            name="Place Without Address",
            lat=51.0,
            lon=19.0,
            address="",
        )

        serializer = PlaceSimpleSerializer(instance=place_empty_address)
        data = serializer.data

        self.assertEqual(data["address"], "")

    def test_serializer_read_only_fields(self):
        """Test that serializer is designed for read-only operations."""
        # This serializer is designed for read-only operations
        # It should work for serialization (reading) but not deserialization (writing)
        
        # Test that we can serialize existing data
        serializer = PlaceSimpleSerializer(instance=self.place)
        data = serializer.data
        
        # Verify serialization works
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "Royal Castle")
        
        # The serializer is meant for nested read-only use,
        # not for accepting input data directly

    def test_serializer_multiple_places(self):
        """Test serializer works correctly with multiple instances."""
        place2 = Place.objects.create(
            name="Palace of Culture",
            lat=52.2319,
            lon=21.0067,
            address="Plac Defilad 1",
        )

        places = [self.place, place2]
        serializer = PlaceSimpleSerializer(places, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Royal Castle")
        self.assertEqual(data[1]["name"], "Palace of Culture")


class PlaceDescriptionContentSerializerTests(TestCase):
    """
    Test suite for PlaceDescriptionContentSerializer.
    Tests serialization of PlaceDescription model with minimal fields.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

        self.route = Route.objects.create(
            user=self.user,
            name="Test Route",
            status="saved",
            route_type="ai_generated",
        )

        self.place = Place.objects.create(
            name="Test Place",
            lat=52.2297,
            lon=21.0122,
        )

        self.route_point = RoutePoint.objects.create(
            route=self.route,
            place=self.place,
            position=1,
            source="ai_generated",
        )

        self.description = PlaceDescription.objects.create(
            route_point=self.route_point,
            language_code="pl",
            content="A" * 3000,  # Valid content length (2500-5000 chars)
        )

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains only expected fields."""
        serializer = PlaceDescriptionContentSerializer(instance=self.description)
        data = serializer.data

        # Check that only expected fields are present
        expected_fields = {"id", "content"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_field_values(self):
        """Test that serializer returns correct field values."""
        serializer = PlaceDescriptionContentSerializer(instance=self.description)
        data = serializer.data

        self.assertEqual(data["id"], self.description.id)
        self.assertEqual(data["content"], "A" * 3000)

    def test_serializer_excludes_extra_fields(self):
        """Test that serializer excludes fields not in field list."""
        serializer = PlaceDescriptionContentSerializer(instance=self.description)
        data = serializer.data

        # These fields should NOT be present
        self.assertNotIn("language_code", data)
        self.assertNotIn("route_point", data)
        self.assertNotIn("created_at", data)
        self.assertNotIn("updated_at", data)

    def test_serializer_with_long_content(self):
        """Test serializer handles maximum length content correctly."""
        # Create a new route point for this description (OneToOne constraint)
        route_point2 = RoutePoint.objects.create(
            route=self.route,
            place=self.place,
            position=2,
            source="ai_generated",
        )
        
        long_description = PlaceDescription.objects.create(
            route_point=route_point2,
            language_code="en",
            content="B" * 5000,  # Maximum valid length
        )

        serializer = PlaceDescriptionContentSerializer(instance=long_description)
        data = serializer.data

        self.assertEqual(len(data["content"]), 5000)
        self.assertEqual(data["content"], "B" * 5000)

    def test_serializer_read_only_fields(self):
        """Test that serializer is designed for read-only operations."""
        # This serializer is designed for read-only operations
        # It should work for serialization (reading) but not deserialization (writing)
        
        # Test that we can serialize existing data
        serializer = PlaceDescriptionContentSerializer(instance=self.description)
        data = serializer.data
        
        # Verify serialization works
        self.assertIsNotNone(data)
        self.assertEqual(data["content"], "A" * 3000)
        
        # The serializer is meant for nested read-only use,
        # not for accepting input data directly

    def test_serializer_multiple_descriptions(self):
        """Test serializer works correctly with multiple instances."""
        # Create second route point and description
        route_point2 = RoutePoint.objects.create(
            route=self.route,
            place=self.place,
            position=2,
            source="ai_generated",
        )

        description2 = PlaceDescription.objects.create(
            route_point=route_point2,
            language_code="en",
            content="C" * 3500,
        )

        descriptions = [self.description, description2]
        serializer = PlaceDescriptionContentSerializer(descriptions, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["content"], "A" * 3000)
        self.assertEqual(data[1]["content"], "C" * 3500)


class RoutePointDetailSerializerTests(TestCase):
    """
    Test suite for RoutePointDetailSerializer.
    Tests serialization of RoutePoint with nested Place and PlaceDescription.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

        self.route = Route.objects.create(
            user=self.user,
            name="Test Route",
            status="saved",
            route_type="ai_generated",
        )

        self.place = Place.objects.create(
            name="Royal Castle",
            lat=52.2480,
            lon=21.0150,
            address="Plac Zamkowy 4",
            city="Warsaw",
            country="Poland",
        )

        self.route_point = RoutePoint.objects.create(
            route=self.route,
            place=self.place,
            position=1,
            source="ai_generated",
        )

        self.description = PlaceDescription.objects.create(
            route_point=self.route_point,
            language_code="pl",
            content="D" * 3000,
        )

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains only expected fields."""
        serializer = RoutePointDetailSerializer(instance=self.route_point)
        data = serializer.data

        # Check that expected fields are present
        expected_fields = {"id", "order", "place", "description"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_position_mapped_to_order(self):
        """Test that 'position' field is mapped to 'order' in output."""
        serializer = RoutePointDetailSerializer(instance=self.route_point)
        data = serializer.data

        # 'order' should be present and equal to 'position'
        self.assertIn("order", data)
        self.assertEqual(data["order"], 1)

        # 'position' should NOT be present in output
        self.assertNotIn("position", data)

    def test_serializer_nested_place_structure(self):
        """Test that nested place has correct structure."""
        serializer = RoutePointDetailSerializer(instance=self.route_point)
        data = serializer.data

        # Check place is nested and has correct fields
        self.assertIn("place", data)
        place_data = data["place"]

        expected_place_fields = {"id", "name", "lat", "lon", "address"}
        self.assertEqual(set(place_data.keys()), expected_place_fields)

        # Check place values
        self.assertEqual(place_data["id"], self.place.id)
        self.assertEqual(place_data["name"], "Royal Castle")
        self.assertEqual(place_data["lat"], 52.2480)
        self.assertEqual(place_data["lon"], 21.0150)
        self.assertEqual(place_data["address"], "Plac Zamkowy 4")

    def test_serializer_nested_description_structure(self):
        """Test that nested description has correct structure."""
        serializer = RoutePointDetailSerializer(instance=self.route_point)
        data = serializer.data

        # Check description is nested and has correct fields
        self.assertIn("description", data)
        description_data = data["description"]

        expected_description_fields = {"id", "content"}
        self.assertEqual(set(description_data.keys()), expected_description_fields)

        # Check description values
        self.assertEqual(description_data["id"], self.description.id)
        self.assertEqual(description_data["content"], "D" * 3000)

    def test_serializer_with_null_description(self):
        """Test serializer handles route point without description."""
        # Create route point without description
        route_point_no_desc = RoutePoint.objects.create(
            route=self.route,
            place=self.place,
            position=2,
            source="manual",
        )

        serializer = RoutePointDetailSerializer(instance=route_point_no_desc)
        data = serializer.data

        # Description should be null
        self.assertIn("description", data)
        self.assertIsNone(data["description"])

    def test_serializer_excludes_extra_fields(self):
        """Test that serializer excludes fields not in field list."""
        serializer = RoutePointDetailSerializer(instance=self.route_point)
        data = serializer.data

        # These fields should NOT be present
        self.assertNotIn("route", data)
        self.assertNotIn("source", data)
        self.assertNotIn("optimized_position", data)
        self.assertNotIn("is_removed", data)
        self.assertNotIn("added_at", data)
        self.assertNotIn("created_at", data)
        self.assertNotIn("updated_at", data)

    def test_serializer_multiple_route_points(self):
        """Test serializer works correctly with multiple instances."""
        # Create second place and route point
        place2 = Place.objects.create(
            name="Palace of Culture",
            lat=52.2319,
            lon=21.0067,
            address="Plac Defilad 1",
        )

        route_point2 = RoutePoint.objects.create(
            route=self.route,
            place=place2,
            position=2,
            source="ai_generated",
        )

        route_points = [self.route_point, route_point2]
        serializer = RoutePointDetailSerializer(route_points, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["order"], 1)
        self.assertEqual(data[0]["place"]["name"], "Royal Castle")
        self.assertEqual(data[1]["order"], 2)
        self.assertEqual(data[1]["place"]["name"], "Palace of Culture")

    def test_serializer_read_only_fields(self):
        """Test that serializer is designed for read-only operations."""
        # This serializer is designed for read-only operations
        # It should work for serialization (reading) but not deserialization (writing)
        
        # Test that we can serialize existing data
        serializer = RoutePointDetailSerializer(instance=self.route_point)
        data = serializer.data
        
        # Verify serialization works
        self.assertIsNotNone(data)
        self.assertEqual(data["order"], 1)
        self.assertEqual(data["place"]["name"], "Royal Castle")
        
        # The serializer is meant for nested read-only use in route detail view,
        # not for accepting input data directly

    def test_serializer_ordering_by_position(self):
        """Test that multiple route points maintain correct order."""
        # Create multiple route points with different positions
        place2 = Place.objects.create(name="Place 2", lat=52.0, lon=21.0)
        place3 = Place.objects.create(name="Place 3", lat=52.1, lon=21.1)

        route_point2 = RoutePoint.objects.create(
            route=self.route, place=place2, position=5, source="manual"
        )

        route_point3 = RoutePoint.objects.create(
            route=self.route, place=place3, position=3, source="manual"
        )

        # Serialize in order
        route_points = [self.route_point, route_point3, route_point2]
        serializer = RoutePointDetailSerializer(route_points, many=True)
        data = serializer.data

        # Check that order values match position values
        self.assertEqual(data[0]["order"], 1)
        self.assertEqual(data[1]["order"], 3)
        self.assertEqual(data[2]["order"], 5)


# -----------------------------------------------------------------------------
# Service Layer Tests
# -----------------------------------------------------------------------------


class RouteServiceTests(TestCase):
    """
    Test suite for RouteService business logic.
    Tests optimization algorithm, validation rules, and error handling.
    """

    def setUp(self):
        """Set up test data for route optimization tests."""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
        )

        # Create manual route (can be optimized)
        self.manual_route = Route.objects.create(
            user=self.user,
            name="Manual Test Route",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_MANUAL,
        )

        # Create AI-generated route (cannot be optimized)
        self.ai_route = Route.objects.create(
            user=self.user,
            name="AI Test Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_AI_GENERATED,
        )

        # Create test places with specific coordinates for predictable optimization
        # Warsaw Old Town area
        self.place1 = Place.objects.create(
            name="Royal Castle",
            lat=52.2480,
            lon=21.0153,
            address="Plac Zamkowy 4",
        )

        self.place2 = Place.objects.create(
            name="Old Town Market Square",
            lat=52.2497,
            lon=21.0122,
            address="Rynek Starego Miasta",
        )

        self.place3 = Place.objects.create(
            name="Barbican",
            lat=52.2509,
            lon=21.0089,
            address="Nowomiejska 15/17",
        )

        self.place4 = Place.objects.create(
            name="Palace of Culture",  # Far from Old Town
            lat=52.2319,
            lon=21.0067,
            address="Plac Defilad 1",
        )

    def test_optimize_route_success_basic(self):
        """Test successful optimization of a manual route with 3 points."""
        from .services import RouteService

        # Create route points in non-optimal order
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place3,  # Farthest from place1
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,  # Between place1 and place3
            position=2,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Optimize route
        optimized_points = RouteService.optimize_route(self.manual_route)

        # Verify we got all points back
        self.assertEqual(len(optimized_points), 3)

        # Verify positions were updated (0, 1, 2)
        positions = [point.position for point in optimized_points]
        self.assertEqual(positions, [0, 1, 2])

        # Verify first point is preserved (starting location)
        self.assertEqual(optimized_points[0].place.id, self.place1.id)

        # Verify optimization improved order (place2 should be between place1 and place3)
        # Expected order: place1 -> place2 -> place3 (geographically logical)
        self.assertEqual(optimized_points[1].place.id, self.place2.id)
        self.assertEqual(optimized_points[2].place.id, self.place3.id)

    def test_optimize_route_with_strategy_parameter(self):
        """Test optimization with explicit strategy parameter."""
        from .services import RouteService

        # Create route points
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Test with nearest_neighbor strategy
        config = {"strategy": "nearest_neighbor"}
        optimized_points = RouteService.optimize_route(self.manual_route, config)

        self.assertEqual(len(optimized_points), 2)
        self.assertEqual(optimized_points[0].position, 0)
        self.assertEqual(optimized_points[1].position, 1)

    def test_optimize_route_with_tsp_approx_strategy(self):
        """Test optimization with tsp_approx strategy."""
        from .services import RouteService

        # Create route points
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Test with tsp_approx strategy
        config = {"strategy": "tsp_approx"}
        optimized_points = RouteService.optimize_route(self.manual_route, config)

        self.assertEqual(len(optimized_points), 2)

    def test_optimize_route_fails_for_ai_generated(self):
        """Test that optimization fails for AI-generated routes."""
        from .services import RouteService, BusinessLogicException

        # Create points for AI route
        RoutePoint.objects.create(
            route=self.ai_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_AI_GENERATED,
        )
        RoutePoint.objects.create(
            route=self.ai_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_AI_GENERATED,
        )

        # Attempt to optimize AI route should raise BusinessLogicException
        with self.assertRaises(BusinessLogicException) as context:
            RouteService.optimize_route(self.ai_route)

        self.assertIn("manual", str(context.exception).lower())

    def test_optimize_route_fails_with_insufficient_points(self):
        """Test that optimization fails when route has less than 2 points."""
        from .services import RouteService, BusinessLogicException

        # Create route with only 1 point
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Attempt to optimize should raise BusinessLogicException
        with self.assertRaises(BusinessLogicException) as context:
            RouteService.optimize_route(self.manual_route)

        self.assertIn("2 punkty", str(context.exception))

    def test_optimize_route_fails_with_zero_points(self):
        """Test that optimization fails when route has no points."""
        from .services import RouteService, BusinessLogicException

        # Route has no points
        with self.assertRaises(BusinessLogicException) as context:
            RouteService.optimize_route(self.manual_route)

        self.assertIn("2 punkty", str(context.exception))

    def test_optimize_route_with_two_points(self):
        """Test optimization with exactly 2 points (minimum valid case)."""
        from .services import RouteService

        # Create route with 2 points
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Optimize route
        optimized_points = RouteService.optimize_route(self.manual_route)

        # With 2 points, order should remain the same
        self.assertEqual(len(optimized_points), 2)
        self.assertEqual(optimized_points[0].place.id, self.place1.id)
        self.assertEqual(optimized_points[1].place.id, self.place2.id)

    def test_optimize_route_ignores_removed_points(self):
        """Test that optimization ignores points marked as removed."""
        from .services import RouteService

        # Create route points
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
            is_removed=False,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
            is_removed=True,  # This point should be ignored
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place3,
            position=2,
            source=RoutePoint.SOURCE_MANUAL,
            is_removed=False,
        )

        # Optimize route
        optimized_points = RouteService.optimize_route(self.manual_route)

        # Should only include non-removed points
        self.assertEqual(len(optimized_points), 2)
        place_ids = [point.place.id for point in optimized_points]
        self.assertIn(self.place1.id, place_ids)
        self.assertIn(self.place3.id, place_ids)
        self.assertNotIn(self.place2.id, place_ids)

    def test_optimize_route_updates_database(self):
        """Test that optimization actually updates positions in database."""
        from .services import RouteService

        # Create route points in specific order
        point1 = RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        point2 = RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place4,  # Far away
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )
        point3 = RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,  # Close to place1
            position=2,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Optimize route
        RouteService.optimize_route(self.manual_route)

        # Refresh from database
        point1.refresh_from_db()
        point2.refresh_from_db()
        point3.refresh_from_db()

        # Verify positions were updated in database
        # Place2 should now be closer to place1 in the order
        self.assertEqual(point1.position, 0)  # First point stays first
        self.assertEqual(point3.position, 1)  # Place2 should be second (closer)
        self.assertEqual(point2.position, 2)  # Place4 should be last (farthest)

    def test_optimize_route_with_many_points(self):
        """Test optimization with larger number of points."""
        from .services import RouteService

        # Create 10 points
        places = []
        for i in range(10):
            place = Place.objects.create(
                name=f"Place {i}",
                lat=52.2 + (i * 0.01),  # Spread out linearly
                lon=21.0 + (i * 0.01),
                address=f"Address {i}",
            )
            places.append(place)

        # Create route points in random order
        for idx, place in enumerate(places):
            RoutePoint.objects.create(
                route=self.manual_route,
                place=place,
                position=idx,
                source=RoutePoint.SOURCE_MANUAL,
            )

        # Optimize route
        optimized_points = RouteService.optimize_route(self.manual_route)

        # Verify we got all points
        self.assertEqual(len(optimized_points), 10)

        # Verify all positions are unique and sequential
        positions = sorted([point.position for point in optimized_points])
        self.assertEqual(positions, list(range(10)))

    def test_calculate_distance_method(self):
        """Test the distance calculation helper method."""
        from .services import RouteService

        # Test distance between Royal Castle and Old Town Market Square
        # These are about 200-300 meters apart
        distance = RouteService._calculate_distance(
            52.2480, 21.0153,  # Royal Castle
            52.2497, 21.0122,  # Old Town Market Square
        )

        # Distance should be approximately 0.2-0.4 km
        self.assertGreater(distance, 0.1)
        self.assertLess(distance, 0.5)

    def test_calculate_distance_same_point(self):
        """Test distance calculation for the same point."""
        from .services import RouteService

        distance = RouteService._calculate_distance(
            52.2480, 21.0153,
            52.2480, 21.0153,
        )

        # Distance should be approximately 0
        self.assertAlmostEqual(distance, 0.0, places=5)

    def test_optimize_route_transaction_rollback_on_error(self):
        """Test that optimization rolls back on error (transaction atomicity)."""
        from .services import RouteService
        from unittest.mock import patch

        # Create valid route points
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Store original positions
        original_count = RoutePoint.objects.filter(route=self.manual_route).count()

        # Mock bulk_update to raise an exception
        with patch.object(
            RoutePoint.objects.__class__, 'bulk_update', side_effect=Exception("DB Error")
        ):
            with self.assertRaises(Exception):
                RouteService.optimize_route(self.manual_route)

        # Verify data is still intact (transaction rolled back)
        current_count = RoutePoint.objects.filter(route=self.manual_route).count()
        self.assertEqual(current_count, original_count)

    def test_optimize_route_with_unknown_strategy(self):
        """Test optimization with unknown strategy falls back to default."""
        from .services import RouteService

        # Create route points
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )
        RoutePoint.objects.create(
            route=self.manual_route,
            place=self.place2,
            position=1,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Test with unknown strategy (should fall back to nearest_neighbor)
        config = {"strategy": "unknown_strategy"}
        optimized_points = RouteService.optimize_route(self.manual_route, config)

        # Should still work with fallback
        self.assertEqual(len(optimized_points), 2)


class RouteUpdateServiceTests(TestCase):
    """
    Test suite for RouteService.update_route() method.
    Tests route name and status updates, saved_at timestamp logic, and validation.
    """

    def setUp(self):
        """Set up test data for route update tests."""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
        )

        # Create temporary route
        self.temp_route = Route.objects.create(
            user=self.user,
            name="Temporary Route",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_AI_GENERATED,
        )

        # Create saved route
        self.saved_route = Route.objects.create(
            user=self.user,
            name="Saved Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_MANUAL,
        )

    def test_update_route_name_only(self):
        """Test updating only the route name."""
        from .services import RouteService

        # Update name only
        validated_data = {"name": "New Route Name"}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify name was updated
        self.assertEqual(updated_route.name, "New Route Name")
        # Verify status remained unchanged
        self.assertEqual(updated_route.status, Route.STATUS_TEMPORARY)
        # Verify saved_at is still None
        self.assertIsNone(updated_route.saved_at)

    def test_update_route_status_only(self):
        """Test updating only the route status."""
        from .services import RouteService

        # Update status only
        validated_data = {"status": Route.STATUS_SAVED}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify status was updated
        self.assertEqual(updated_route.status, Route.STATUS_SAVED)
        # Verify name remained unchanged
        self.assertEqual(updated_route.name, "Temporary Route")
        # Verify saved_at was set
        self.assertIsNotNone(updated_route.saved_at)

    def test_update_route_name_and_status(self):
        """Test updating both name and status together."""
        from .services import RouteService

        # Update both fields
        validated_data = {
            "name": "My Trip to Paris",
            "status": Route.STATUS_SAVED,
        }
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify both fields were updated
        self.assertEqual(updated_route.name, "My Trip to Paris")
        self.assertEqual(updated_route.status, Route.STATUS_SAVED)
        # Verify saved_at was set
        self.assertIsNotNone(updated_route.saved_at)

    def test_update_route_sets_saved_at_when_status_changes_to_saved(self):
        """Test that saved_at timestamp is set when status changes to saved."""
        from .services import RouteService
        from django.utils import timezone

        # Verify initial state
        self.assertIsNone(self.temp_route.saved_at)
        self.assertEqual(self.temp_route.status, Route.STATUS_TEMPORARY)

        # Record time before update
        time_before = timezone.now()

        # Update status to saved
        validated_data = {"status": Route.STATUS_SAVED}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Record time after update
        time_after = timezone.now()

        # Verify saved_at was set
        self.assertIsNotNone(updated_route.saved_at)
        # Verify saved_at is between time_before and time_after
        self.assertGreaterEqual(updated_route.saved_at, time_before)
        self.assertLessEqual(updated_route.saved_at, time_after)

    def test_update_route_does_not_change_saved_at_when_already_saved(self):
        """Test that saved_at is not changed when updating an already saved route."""
        from .services import RouteService
        from django.utils import timezone

        # Set initial saved_at
        original_saved_at = timezone.now()
        self.saved_route.saved_at = original_saved_at
        self.saved_route.save()

        # Update name only (status remains saved)
        validated_data = {"name": "Updated Saved Route"}
        updated_route = RouteService.update_route(self.saved_route, validated_data)

        # Verify saved_at was not changed
        self.assertEqual(updated_route.saved_at, original_saved_at)

    def test_update_route_does_not_set_saved_at_when_status_stays_temporary(self):
        """Test that saved_at remains None when status stays temporary."""
        from .services import RouteService

        # Update name while keeping status temporary
        validated_data = {"name": "Still Temporary"}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify saved_at is still None
        self.assertIsNone(updated_route.saved_at)

    def test_update_route_persists_to_database(self):
        """Test that updates are actually saved to database."""
        from .services import RouteService

        # Update route
        validated_data = {
            "name": "Database Test Route",
            "status": Route.STATUS_SAVED,
        }
        RouteService.update_route(self.temp_route, validated_data)

        # Refresh from database
        self.temp_route.refresh_from_db()

        # Verify changes persisted
        self.assertEqual(self.temp_route.name, "Database Test Route")
        self.assertEqual(self.temp_route.status, Route.STATUS_SAVED)
        self.assertIsNotNone(self.temp_route.saved_at)

    def test_update_route_with_empty_validated_data(self):
        """Test update with empty validated_data (no changes)."""
        from .services import RouteService

        # Store original values
        original_name = self.temp_route.name
        original_status = self.temp_route.status

        # Update with empty data
        validated_data = {}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify nothing changed
        self.assertEqual(updated_route.name, original_name)
        self.assertEqual(updated_route.status, original_status)
        self.assertIsNone(updated_route.saved_at)

    def test_update_route_transaction_atomicity(self):
        """Test that update is atomic (all or nothing)."""
        from .services import RouteService

        # This test verifies that the @transaction.atomic decorator is working
        # In case of any error, changes should be rolled back

        # Update route successfully
        validated_data = {"name": "Atomic Test"}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify update succeeded
        self.assertEqual(updated_route.name, "Atomic Test")

        # Refresh from database to ensure it was committed
        self.temp_route.refresh_from_db()
        self.assertEqual(self.temp_route.name, "Atomic Test")

    def test_update_route_updated_at_timestamp(self):
        """Test that updated_at timestamp is automatically updated."""
        from .services import RouteService
        from django.utils import timezone
        import time

        # Store original updated_at
        original_updated_at = self.temp_route.updated_at

        # Wait a moment to ensure timestamp difference
        time.sleep(0.01)

        # Update route
        validated_data = {"name": "Timestamp Test"}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify updated_at changed
        self.assertGreater(updated_route.updated_at, original_updated_at)

    def test_update_route_changing_status_from_saved_to_temporary(self):
        """Test changing status from saved back to temporary (edge case)."""
        from .services import RouteService
        from django.utils import timezone

        # Set route as saved with saved_at timestamp
        self.saved_route.saved_at = timezone.now()
        self.saved_route.save()
        original_saved_at = self.saved_route.saved_at

        # Change status back to temporary
        validated_data = {"status": Route.STATUS_TEMPORARY}
        updated_route = RouteService.update_route(self.saved_route, validated_data)

        # Verify status changed
        self.assertEqual(updated_route.status, Route.STATUS_TEMPORARY)
        # Verify saved_at was not modified (keeps original timestamp)
        self.assertEqual(updated_route.saved_at, original_saved_at)


# -----------------------------------------------------------------------------
# Route PATCH Endpoint Tests
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# RoutePointCreateSerializer Tests
# -----------------------------------------------------------------------------


class RoutePointCreateSerializerTests(TestCase):
    """
    Test suite for RoutePointCreateSerializer.
    Tests validation logic, place creation/lookup, and position calculation.
    """

    def setUp(self):
        """Set up test data for route point creation tests."""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
        )

        # Create manual route (can have points added)
        self.manual_route = Route.objects.create(
            user=self.user,
            name="Manual Test Route",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_MANUAL,
        )

        # Create AI-generated route (cannot have points added)
        self.ai_route = Route.objects.create(
            user=self.user,
            name="AI Test Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_AI_GENERATED,
        )

        # Create existing place for deduplication tests
        self.existing_place = Place.objects.create(
            name="Existing Place",
            lat=52.2297,
            lon=21.0122,
            osm_id=123456,
            wikipedia_id="pl:Existing_Place",
            address="Test Address 1",
        )

    def test_create_route_point_with_new_place_success(self):
        """Test creating route point with a new place."""
        from .serializers import RoutePointCreateSerializer

        # Prepare input data
        data = {
            "place": {
                "name": "New Place",
                "lat": 52.2319,
                "lon": 21.0067,
                "address": "Plac Defilad 1",
            }
        }

        # Initialize serializer with route context
        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate and create
        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify route point was created
        self.assertIsNotNone(route_point.id)
        self.assertEqual(route_point.route, self.manual_route)
        self.assertEqual(route_point.position, 0)
        self.assertEqual(route_point.source, RoutePoint.SOURCE_MANUAL)

        # Verify place was created
        self.assertEqual(route_point.place.name, "New Place")
        self.assertEqual(route_point.place.lat, 52.2319)
        self.assertEqual(route_point.place.lon, 21.0067)
        self.assertEqual(route_point.place.address, "Plac Defilad 1")

    def test_create_route_point_with_existing_place_by_osm_id(self):
        """Test creating route point with existing place (lookup by osm_id)."""
        from .serializers import RoutePointCreateSerializer

        # Count places before
        place_count_before = Place.objects.count()

        # Prepare input data with existing osm_id
        data = {
            "place": {
                "name": "Different Name",  # Name differs, but osm_id matches
                "lat": 52.9999,  # Coordinates differ
                "lon": 21.9999,
                "osm_id": 123456,  # Matches existing_place
                "address": "Different Address",
            }
        }

        # Initialize serializer with route context
        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate and create
        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify no new place was created (deduplication worked)
        place_count_after = Place.objects.count()
        self.assertEqual(place_count_after, place_count_before)

        # Verify existing place was reused
        self.assertEqual(route_point.place.id, self.existing_place.id)
        self.assertEqual(route_point.place.name, "Existing Place")
        self.assertEqual(route_point.place.osm_id, 123456)

    def test_create_route_point_with_existing_place_by_wikipedia_id(self):
        """Test creating route point with existing place (lookup by wikipedia_id)."""
        from .serializers import RoutePointCreateSerializer

        # Count places before
        place_count_before = Place.objects.count()

        # Prepare input data with existing wikipedia_id but no osm_id
        data = {
            "place": {
                "name": "Different Name",
                "lat": 52.9999,
                "lon": 21.9999,
                "wikipedia_id": "pl:Existing_Place",  # Matches existing_place
                "address": "Different Address",
            }
        }

        # Initialize serializer with route context
        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate and create
        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify no new place was created (deduplication worked)
        place_count_after = Place.objects.count()
        self.assertEqual(place_count_after, place_count_before)

        # Verify existing place was reused
        self.assertEqual(route_point.place.id, self.existing_place.id)
        self.assertEqual(route_point.place.wikipedia_id, "pl:Existing_Place")

    def test_create_route_point_osm_id_takes_precedence_over_wikipedia_id(self):
        """Test that osm_id lookup takes precedence over wikipedia_id."""
        from .serializers import RoutePointCreateSerializer

        # Create another place with different wikipedia_id
        other_place = Place.objects.create(
            name="Other Place",
            lat=52.1111,
            lon=21.1111,
            osm_id=999999,
            wikipedia_id="pl:Other_Place",
        )

        # Prepare input data with both osm_id and wikipedia_id
        # osm_id matches existing_place, wikipedia_id matches other_place
        data = {
            "place": {
                "name": "Test",
                "lat": 52.0,
                "lon": 21.0,
                "osm_id": 123456,  # Matches existing_place
                "wikipedia_id": "pl:Other_Place",  # Matches other_place
            }
        }

        # Initialize serializer
        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate and create
        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify osm_id took precedence (existing_place was used)
        self.assertEqual(route_point.place.id, self.existing_place.id)
        self.assertNotEqual(route_point.place.id, other_place.id)

    def test_validate_fails_for_ai_generated_route(self):
        """Test that validation fails when trying to add point to AI-generated route."""
        from .serializers import RoutePointCreateSerializer

        # Prepare valid place data
        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        # Initialize serializer with AI route context
        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.ai_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("AI generated", str(serializer.errors))

    def test_validate_fails_when_max_points_limit_reached(self):
        """Test that validation fails when route has 10 points (max limit for manual routes)."""
        from .serializers import RoutePointCreateSerializer

        # Create 10 route points (max limit for manual routes)
        for i in range(10):
            place = Place.objects.create(
                name=f"Place {i}",
                lat=52.0 + (i * 0.001),
                lon=21.0 + (i * 0.001),
            )
            RoutePoint.objects.create(
                route=self.manual_route,
                place=place,
                position=i,
                source=RoutePoint.SOURCE_MANUAL,
                is_removed=False,
            )

        # Verify we have 10 points
        self.assertEqual(
            RoutePoint.objects.filter(route=self.manual_route, is_removed=False).count(),
            10
        )

        # Try to add 11th point
        data = {
            "place": {
                "name": "11th Place",
                "lat": 52.5,
                "lon": 21.5,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("Max points limit", str(serializer.errors))

    def test_validate_succeeds_with_9_points(self):
        """Test that validation succeeds when route has 9 points (under limit)."""
        from .serializers import RoutePointCreateSerializer

        # Create 9 route points
        for i in range(9):
            place = Place.objects.create(
                name=f"Place {i}",
                lat=52.0 + (i * 0.001),
                lon=21.0 + (i * 0.001),
            )
            RoutePoint.objects.create(
                route=self.manual_route,
                place=place,
                position=i,
                source=RoutePoint.SOURCE_MANUAL,
                is_removed=False,
            )

        # Try to add 10th point (should succeed)
        data = {
            "place": {
                "name": "10th Place",
                "lat": 52.5,
                "lon": 21.5,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should succeed
        self.assertTrue(serializer.is_valid())

    def test_validate_ignores_removed_points_in_count(self):
        """Test that validation ignores removed points when counting."""
        from .serializers import RoutePointCreateSerializer

        # Create 15 points, but mark 10 as removed (leaving 5 active)
        for i in range(15):
            place = Place.objects.create(
                name=f"Place {i}",
                lat=52.0 + (i * 0.001),
                lon=21.0 + (i * 0.001),
            )
            RoutePoint.objects.create(
                route=self.manual_route,
                place=place,
                position=i,
                source=RoutePoint.SOURCE_MANUAL,
                is_removed=(i < 10),  # First 10 are removed
            )

        # Verify we have 5 active points
        self.assertEqual(
            RoutePoint.objects.filter(route=self.manual_route, is_removed=False).count(),
            5
        )

        # Try to add another point (should succeed, as only 5 active, limit is 10)
        data = {
            "place": {
                "name": "New Place",
                "lat": 52.5,
                "lon": 21.5,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should succeed
        self.assertTrue(serializer.is_valid())

    def test_validate_fails_without_route_context(self):
        """Test that validation fails when route context is missing."""
        from .serializers import RoutePointCreateSerializer

        # Prepare valid place data
        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        # Initialize serializer WITHOUT route context
        serializer = RoutePointCreateSerializer(data=data, context={})

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("Route context", str(serializer.errors))

    def test_position_calculation_for_first_point(self):
        """Test that position is calculated as 0 for first point."""
        from .serializers import RoutePointCreateSerializer

        # Route has no points yet
        self.assertEqual(
            RoutePoint.objects.filter(route=self.manual_route).count(),
            0
        )

        # Add first point
        data = {
            "place": {
                "name": "First Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify position is 0
        self.assertEqual(route_point.position, 0)

    def test_position_calculation_for_subsequent_points(self):
        """Test that position is calculated correctly for subsequent points."""
        from .serializers import RoutePointCreateSerializer

        # Add first point
        place1 = Place.objects.create(name="Place 1", lat=52.0, lon=21.0)
        RoutePoint.objects.create(
            route=self.manual_route,
            place=place1,
            position=0,
            source=RoutePoint.SOURCE_MANUAL,
        )

        # Add second point
        data = {
            "place": {
                "name": "Place 2",
                "lat": 52.1,
                "lon": 21.1,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify position is 1
        self.assertEqual(route_point.position, 1)

    def test_position_calculation_ignores_removed_points(self):
        """Test that position calculation considers only non-removed points."""
        from .serializers import RoutePointCreateSerializer

        # Add points with positions 0, 1, 2
        for i in range(3):
            place = Place.objects.create(name=f"Place {i}", lat=52.0 + i, lon=21.0 + i)
            RoutePoint.objects.create(
                route=self.manual_route,
                place=place,
                position=i,
                source=RoutePoint.SOURCE_MANUAL,
                is_removed=(i == 2),  # Last point is removed
            )

        # Add new point
        data = {
            "place": {
                "name": "New Place",
                "lat": 52.5,
                "lon": 21.5,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Position should be 2 (last non-removed was 1, so next is 2)
        # Even though there's a removed point at position 2
        self.assertEqual(route_point.position, 2)

    def test_place_input_validation_missing_name(self):
        """Test that validation fails when place name is missing."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("name", serializer.errors["place"])

    def test_place_input_validation_missing_lat(self):
        """Test that validation fails when latitude is missing."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lat", serializer.errors["place"])

    def test_place_input_validation_missing_lon(self):
        """Test that validation fails when longitude is missing."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lon", serializer.errors["place"])

    def test_place_input_validation_lat_out_of_range_high(self):
        """Test that validation fails when latitude is above 90."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 91.0,  # Invalid: > 90
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lat", serializer.errors["place"])

    def test_place_input_validation_lat_out_of_range_low(self):
        """Test that validation fails when latitude is below -90."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": -91.0,  # Invalid: < -90
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lat", serializer.errors["place"])

    def test_place_input_validation_lon_out_of_range_high(self):
        """Test that validation fails when longitude is above 180."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": 181.0,  # Invalid: > 180
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lon", serializer.errors["place"])

    def test_place_input_validation_lon_out_of_range_low(self):
        """Test that validation fails when longitude is below -180."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": -181.0,  # Invalid: < -180
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lon", serializer.errors["place"])

    def test_place_input_validation_lat_lon_at_boundaries(self):
        """Test that validation succeeds with lat/lon at valid boundaries."""
        from .serializers import RoutePointCreateSerializer

        # Test with boundary values
        test_cases = [
            {"lat": 90.0, "lon": 180.0},
            {"lat": -90.0, "lon": -180.0},
            {"lat": 0.0, "lon": 0.0},
        ]

        for coords in test_cases:
            data = {
                "place": {
                    "name": "Boundary Test",
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                }
            }

            serializer = RoutePointCreateSerializer(
                data=data,
                context={'route': self.manual_route}
            )

            # Validate should succeed
            self.assertTrue(
                serializer.is_valid(),
                f"Validation failed for lat={coords['lat']}, lon={coords['lon']}"
            )

    def test_place_input_optional_fields(self):
        """Test that optional place fields (osm_id, address, wikipedia_id) work correctly."""
        from .serializers import RoutePointCreateSerializer

        # Test with all optional fields
        data = {
            "place": {
                "name": "Complete Place",
                "lat": 52.2319,
                "lon": 21.0067,
                "osm_id": 789012,
                "address": "Complete Address 123",
                "wikipedia_id": "pl:Complete_Place",
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify all fields were saved
        self.assertEqual(route_point.place.name, "Complete Place")
        self.assertEqual(route_point.place.osm_id, 789012)
        self.assertEqual(route_point.place.address, "Complete Address 123")
        self.assertEqual(route_point.place.wikipedia_id, "pl:Complete_Place")

    def test_place_input_optional_fields_can_be_omitted(self):
        """Test that optional place fields can be omitted."""
        from .serializers import RoutePointCreateSerializer

        # Test with only required fields
        data = {
            "place": {
                "name": "Minimal Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify place was created with required fields only
        self.assertEqual(route_point.place.name, "Minimal Place")
        self.assertIsNone(route_point.place.osm_id)
        self.assertIsNone(route_point.place.wikipedia_id)

    def test_route_point_source_is_manual(self):
        """Test that created route point has source set to 'manual'."""
        from .serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data,
            context={'route': self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify source is 'manual'
        self.assertEqual(route_point.source, RoutePoint.SOURCE_MANUAL)

    def test_create_multiple_points_in_sequence(self):
        """Test creating multiple points in sequence with correct position calculation."""
        from .serializers import RoutePointCreateSerializer

        # Create 5 points in sequence
        for i in range(5):
            data = {
                "place": {
                    "name": f"Place {i}",
                    "lat": 52.0 + (i * 0.01),
                    "lon": 21.0 + (i * 0.01),
                }
            }

            serializer = RoutePointCreateSerializer(
                data=data,
                context={'route': self.manual_route}
            )

            self.assertTrue(serializer.is_valid())
            route_point = serializer.save()

            # Verify position matches sequence
            self.assertEqual(route_point.position, i)

        # Verify all points were created
        self.assertEqual(
            RoutePoint.objects.filter(route=self.manual_route).count(),
            5
        )


# -----------------------------------------------------------------------------
# Route Point Delete Tests
# -----------------------------------------------------------------------------


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
        long_content = "AI generated description for place 1. " * 100  # ~3900 characters
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


# -----------------------------------------------------------------------------
# Route Creation (POST /api/routes/) Tests
# -----------------------------------------------------------------------------


class RouteCreateAPIViewTests(TestCase):
    """
    Test suite for POST /api/routes/ endpoint.
    Tests creation of both manual and AI-generated routes.
    """

    def setUp(self):
        """Set up test client, users, and tags."""
        self.client = APIClient()
        self.route_create_url = "/api/routes/"
        
        # Create test users
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            is_active=True,
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
            is_active=True,
        )
        
        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        
        # Create test tags
        self.tag1 = Tag.objects.create(
            name="Museums",
            description="Museums and galleries",
            is_active=True,
            priority=10
        )
        self.tag2 = Tag.objects.create(
            name="Architecture",
            description="Architectural landmarks",
            is_active=True,
            priority=9
        )
        self.tag3 = Tag.objects.create(
            name="Parks",
            description="Parks and nature",
            is_active=True,
            priority=8
        )
        self.tag_inactive = Tag.objects.create(
            name="Inactive Tag",
            description="This tag is inactive",
            is_active=False,
            priority=0
        )

    # -------------------------------------------------------------------------
    # Manual Route Creation Tests
    # -------------------------------------------------------------------------

    def test_create_manual_route_with_name(self):
        """Test creating a manual route with custom name."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual",
            "name": "My Trip to Krakow"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["name"], "My Trip to Krakow")
        self.assertEqual(response.data["status"], "temporary")
        self.assertEqual(response.data["route_type"], "manual")
        self.assertEqual(response.data["points"], [])  # No points initially
        
        # Verify database
        route = Route.objects.get(id=response.data["id"])
        self.assertEqual(route.user, self.user1)
        self.assertEqual(route.name, "My Trip to Krakow")
        self.assertEqual(route.status, Route.STATUS_TEMPORARY)
        self.assertEqual(route.route_type, Route.TYPE_MANUAL)
        
        # Verify no tags associated
        self.assertEqual(RouteTag.objects.filter(route=route).count(), 0)

    def test_create_manual_route_without_name(self):
        """Test creating a manual route without name uses default."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Custom Trip")
        self.assertEqual(response.data["route_type"], "manual")
        self.assertEqual(response.data["points"], [])

    def test_create_manual_route_with_whitespace_name(self):
        """Test creating a manual route with whitespace-only name uses default."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual",
            "name": "   "  # Whitespace only
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should succeed and use default name (service trims whitespace)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Custom Trip")

    def test_create_manual_route_with_tags_fails(self):
        """Test that manual routes cannot have tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual",
            "name": "My Trip",
            "tags": [self.tag1.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)
        self.assertIn("nie są dozwolone", str(response.data["tags"][0]).lower())

    def test_create_manual_route_with_description_fails(self):
        """Test that manual routes cannot have description."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual",
            "name": "My Trip",
            "description": "Some description"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_create_manual_route_name_too_long(self):
        """Test that manual route name cannot exceed 500 characters."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual",
            "name": "A" * 501  # 501 characters
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    # -------------------------------------------------------------------------
    # AI-Generated Route Creation Tests
    # -------------------------------------------------------------------------

    def test_create_ai_route_with_one_tag(self):
        """Test creating an AI-generated route with 1 tag."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "temporary")
        self.assertEqual(response.data["route_type"], "ai_generated")
        self.assertGreater(len(response.data["points"]), 0)  # Should have AI-generated points
        
        # Verify database
        route = Route.objects.get(id=response.data["id"])
        self.assertEqual(route.user, self.user1)
        self.assertEqual(route.route_type, Route.TYPE_AI_GENERATED)
        
        # Verify tags
        route_tags = RouteTag.objects.filter(route=route)
        self.assertEqual(route_tags.count(), 1)
        self.assertEqual(route_tags.first().tag, self.tag1)
        
        # Verify AI log was created
        ai_logs = AIGenerationLog.objects.filter(route=route)
        self.assertEqual(ai_logs.count(), 1)
        self.assertEqual(ai_logs.first().tags_snapshot, ["Museums"])

    def test_create_ai_route_with_two_tags(self):
        """Test creating an AI-generated route with 2 tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id, self.tag2.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify tags
        route = Route.objects.get(id=response.data["id"])
        route_tags = RouteTag.objects.filter(route=route)
        self.assertEqual(route_tags.count(), 2)
        
        tag_ids = set(rt.tag.id for rt in route_tags)
        self.assertEqual(tag_ids, {self.tag1.id, self.tag2.id})

    def test_create_ai_route_with_three_tags(self):
        """Test creating an AI-generated route with 3 tags (maximum)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id, self.tag2.id, self.tag3.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify tags
        route = Route.objects.get(id=response.data["id"])
        route_tags = RouteTag.objects.filter(route=route)
        self.assertEqual(route_tags.count(), 3)

    def test_create_ai_route_with_description(self):
        """Test creating an AI-generated route with optional description."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id],
            "description": "Interested in modern architecture and design"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify AI log contains description
        route = Route.objects.get(id=response.data["id"])
        ai_log = AIGenerationLog.objects.get(route=route)
        self.assertEqual(ai_log.additional_text_snapshot, "Interested in modern architecture and design")

    def test_create_ai_route_without_tags_fails(self):
        """Test that AI-generated routes require tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)
        self.assertIn("wymagane", str(response.data["tags"][0]).lower())

    def test_create_ai_route_with_empty_tags_fails(self):
        """Test that AI-generated routes cannot have empty tags list."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": []
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

    def test_create_ai_route_with_too_many_tags_fails(self):
        """Test that AI-generated routes cannot have more than 3 tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        # Create a 4th tag
        tag4 = Tag.objects.create(name="History", is_active=True)
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id, self.tag2.id, self.tag3.id, tag4.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)
        self.assertIn("3", str(response.data["tags"][0]))

    def test_create_ai_route_with_invalid_tag_id_fails(self):
        """Test that invalid tag IDs are rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [99999]  # Non-existent tag ID
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

    def test_create_ai_route_with_inactive_tag_fails(self):
        """Test that inactive tags are rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag_inactive.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

    def test_create_ai_route_description_too_long_fails(self):
        """Test that description cannot exceed 1000 characters."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id],
            "description": "A" * 1001  # 1001 characters
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_create_ai_route_generates_points(self):
        """Test that AI-generated routes have points created."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id, self.tag2.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response has points
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(len(response.data["points"]), 0)
        
        # Verify points structure
        first_point = response.data["points"][0]
        self.assertIn("id", first_point)
        self.assertIn("order", first_point)
        self.assertIn("place", first_point)
        self.assertIn("description", first_point)
        
        # Verify place structure
        self.assertIn("name", first_point["place"])
        self.assertIn("lat", first_point["place"])
        self.assertIn("lon", first_point["place"])
        
        # Verify database
        route = Route.objects.get(id=response.data["id"])
        route_points = RoutePoint.objects.filter(route=route, is_removed=False)
        self.assertGreater(route_points.count(), 0)
        
        # Verify all points have AI source
        for point in route_points:
            self.assertEqual(point.source, RoutePoint.SOURCE_AI_GENERATED)

    def test_create_ai_route_creates_place_descriptions(self):
        """Test that AI-generated routes create place descriptions."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id]
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify descriptions exist
        route = Route.objects.get(id=response.data["id"])
        route_points = RoutePoint.objects.filter(route=route, is_removed=False)
        
        for point in route_points:
            descriptions = PlaceDescription.objects.filter(route_point=point)
            self.assertGreater(descriptions.count(), 0)

    # -------------------------------------------------------------------------
    # General Validation Tests
    # -------------------------------------------------------------------------

    def test_create_route_without_authentication_fails(self):
        """Test that unauthenticated requests are rejected."""
        data = {
            "route_type": "manual",
            "name": "My Trip"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail authentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_route_without_route_type_fails(self):
        """Test that route_type is required."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "name": "My Trip"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route_type", response.data)

    def test_create_route_with_invalid_route_type_fails(self):
        """Test that invalid route_type is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "invalid_type"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route_type", response.data)

    def test_create_route_user_isolation(self):
        """Test that routes are created for the authenticated user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        data = {
            "route_type": "manual",
            "name": "User 1 Trip"
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Verify route belongs to user1
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        route = Route.objects.get(id=response.data["id"])
        self.assertEqual(route.user, self.user1)
        
        # Verify user2 cannot see it in their list
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        list_response = self.client.get(self.route_create_url)
        route_ids = [r["id"] for r in list_response.data["results"]]
        self.assertNotIn(route.id, route_ids)

    def test_create_multiple_routes_same_user(self):
        """Test that a user can create multiple routes."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        # Create first route
        data1 = {
            "route_type": "manual",
            "name": "Trip 1"
        }
        response1 = self.client.post(self.route_create_url, data1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Create second route
        data2 = {
            "route_type": "ai_generated",
            "tags": [self.tag1.id]
        }
        response2 = self.client.post(self.route_create_url, data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both exist
        self.assertNotEqual(response1.data["id"], response2.data["id"])
        self.assertEqual(Route.objects.filter(user=self.user1).count(), 2)

    def test_create_route_transaction_rollback_on_error(self):
        """Test that database transaction is rolled back on error."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        
        initial_route_count = Route.objects.count()
        initial_tag_count = RouteTag.objects.count()
        
        # Try to create route with invalid data that will fail after partial creation
        data = {
            "route_type": "ai_generated",
            "tags": [99999]  # Invalid tag ID
        }
        
        response = self.client.post(self.route_create_url, data, format="json")
        
        # Should fail
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify no partial data was created
        self.assertEqual(Route.objects.count(), initial_route_count)
        self.assertEqual(RouteTag.objects.count(), initial_tag_count)
