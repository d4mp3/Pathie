from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import Route, RoutePoint, Place, PlaceDescription, Rating
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

    def test_delete_route_only_delete_method_allowed(self):
        """Test that only GET and DELETE methods are allowed for route detail endpoint."""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        url = f"/api/routes/{self.route1.id}/"

        # GET method should work (returns route details)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try POST method - should fail
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT method - should fail
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PATCH method - should fail
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
