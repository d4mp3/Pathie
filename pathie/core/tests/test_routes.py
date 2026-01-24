from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from ..models import (
    Route,
    RoutePoint,
    Place,
    Tag,
    RouteTag,
    AIGenerationLog,
    PlaceDescription,
)

User = get_user_model()


class RouteListAPIViewTests(TestCase):
    """
    Test suite for route list endpoint.
    Tests GET /api/routes/ endpoint functionality including filtering,
    ordering, pagination, and data isolation.
    """

    def setUp(self):
        """Set up test client, users, and test routes."""
        self.client = APIClient()
        self.route_list_url = "/api/routes/"

        # Create test users
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

        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Create test routes for user1
        self.route1_saved = Route.objects.create(
            user=self.user1,
            name="Saved Route 1",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_AI_GENERATED,
        )
        self.route2_saved = Route.objects.create(
            user=self.user1,
            name="Saved Route 2",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_MANUAL,
        )
        self.route3_saved = Route.objects.create(
            user=self.user1,
            name="Saved Route 3",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_AI_GENERATED,
        )
        self.route4_temporary = Route.objects.create(
            user=self.user1,
            name="Temporary Route 1",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_MANUAL,
        )
        self.route5_temporary = Route.objects.create(
            user=self.user1,
            name="Temporary Route 2",
            status=Route.STATUS_TEMPORARY,
            route_type=Route.TYPE_MANUAL,
        )

        # Create test routes for user2
        self.route6_user2 = Route.objects.create(
            user=self.user2,
            name="User2 Route",
            status=Route.STATUS_SAVED,
            route_type=Route.TYPE_MANUAL,
        )

        # Create test places
        self.place1 = Place.objects.create(
            name="Test Place 1",
            lat=52.2297,
            lon=21.0122,
            address="Test Address 1",
        )
        self.place2 = Place.objects.create(
            name="Test Place 2",
            lat=52.2298,
            lon=21.0123,
            address="Test Address 2",
        )

        # Add route points to some routes
        RoutePoint.objects.create(
            route=self.route1_saved,
            place=self.place1,
            source=RoutePoint.SOURCE_MANUAL,
            position=0,
            is_removed=False,
        )
        RoutePoint.objects.create(
            route=self.route1_saved,
            place=self.place2,
            source=RoutePoint.SOURCE_MANUAL,
            position=1,
            is_removed=False,
        )
        RoutePoint.objects.create(
            route=self.route2_saved,
            place=self.place1,
            source=RoutePoint.SOURCE_MANUAL,
            position=0,
            is_removed=False,
        )
        # Add removed point (should not be counted)
        RoutePoint.objects.create(
            route=self.route2_saved,
            place=self.place2,
            source=RoutePoint.SOURCE_MANUAL,
            position=1,
            is_removed=True,
        )

    def test_list_routes_success_default_parameters(self):
        """Test successful request with default parameters returns saved routes."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(self.route_list_url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

        # Verify count (only saved routes)
        self.assertEqual(response.data["count"], 3)

        # Verify all results are saved routes
        for route in response.data["results"]:
            self.assertEqual(route["status"], "saved")

        # Verify ordering (default is -created_at, newest first)
        route_ids = [r["id"] for r in response.data["results"]]
        self.assertEqual(
            route_ids,
            [self.route3_saved.id, self.route2_saved.id, self.route1_saved.id],
        )

    def test_list_routes_unauthorized(self):
        """Test unauthorized access returns 401."""
        response = self.client.get(self.route_list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_list_routes_filter_by_status_temporary(self):
        """Test filtering routes by temporary status."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?status=temporary")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

        # Verify all results are temporary routes
        for route in response.data["results"]:
            self.assertEqual(route["status"], "temporary")

    def test_list_routes_filter_by_status_saved(self):
        """Test explicitly filtering routes by saved status."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?status=saved")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        # Verify all results are saved routes
        for route in response.data["results"]:
            self.assertEqual(route["status"], "saved")

    def test_list_routes_invalid_status_fallback_to_default(self):
        """Test that invalid status value falls back to default (saved)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?status=invalid_status")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        # Verify all results are saved routes (default)
        for route in response.data["results"]:
            self.assertEqual(route["status"], "saved")

    def test_list_routes_ordering_by_name_ascending(self):
        """Test ordering routes by name in ascending order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?status=saved&ordering=name")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        # Verify ordering
        route_names = [r["name"] for r in response.data["results"]]
        self.assertEqual(
            route_names, ["Saved Route 1", "Saved Route 2", "Saved Route 3"]
        )

    def test_list_routes_ordering_by_name_descending(self):
        """Test ordering routes by name in descending order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?status=saved&ordering=-name")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        # Verify ordering
        route_names = [r["name"] for r in response.data["results"]]
        self.assertEqual(
            route_names, ["Saved Route 3", "Saved Route 2", "Saved Route 1"]
        )

    def test_list_routes_ordering_by_points_count_descending(self):
        """Test ordering routes by points count in descending order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(
            f"{self.route_list_url}?status=saved&ordering=-points_count"
        )

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify points_count field is present
        for route in response.data["results"]:
            self.assertIn("points_count", route)

        # Verify ordering (route1 has 2 points, route2 has 1 point (1 removed), route3 has 0 points)
        route_ids = [r["id"] for r in response.data["results"]]
        points_counts = [r["points_count"] for r in response.data["results"]]

        self.assertEqual(route_ids[0], self.route1_saved.id)
        self.assertEqual(points_counts[0], 2)
        self.assertEqual(route_ids[1], self.route2_saved.id)
        self.assertEqual(points_counts[1], 1)  # Removed point not counted
        self.assertEqual(route_ids[2], self.route3_saved.id)
        self.assertEqual(points_counts[2], 0)

    def test_list_routes_pagination_page_1(self):
        """Test pagination returns correct first page."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?page=1&page_size=2")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_list_routes_pagination_page_2(self):
        """Test pagination returns correct second page."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?page=2&page_size=2")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 1)  # Last page has 1 item
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_list_routes_pagination_page_out_of_range(self):
        """Test that requesting page out of range returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?page=999")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_list_routes_data_isolation_between_users(self):
        """Test that users only see their own routes."""
        # User1 should see 3 saved routes
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response1 = self.client.get(self.route_list_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["count"], 3)

        # User2 should see 1 saved route
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        response2 = self.client.get(self.route_list_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["count"], 1)
        self.assertEqual(response2.data["results"][0]["id"], self.route6_user2.id)

    def test_list_routes_response_fields(self):
        """Test that response contains all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(self.route_list_url)

        # Verify response structure
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify route object fields
        route = response.data["results"][0]
        self.assertIn("id", route)
        self.assertIn("name", route)
        self.assertIn("status", route)
        self.assertIn("route_type", route)
        self.assertIn("created_at", route)
        self.assertIn("points_count", route)

        # Verify field types
        self.assertIsInstance(route["id"], int)
        self.assertIsInstance(route["name"], str)
        self.assertIsInstance(route["status"], str)
        self.assertIsInstance(route["route_type"], str)
        self.assertIsInstance(route["created_at"], str)
        self.assertIsInstance(route["points_count"], int)

    def test_list_routes_points_count_excludes_removed_points(self):
        """Test that points_count annotation excludes removed points."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        response = self.client.get(f"{self.route_list_url}?ordering=name")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find route2 in results (has 1 active point and 1 removed point)
        route2_data = next(
            r for r in response.data["results"] if r["id"] == self.route2_saved.id
        )

        # Verify points_count excludes removed point
        self.assertEqual(route2_data["points_count"], 1)  # Should be 1, not 2

    def test_list_routes_empty_results_for_new_user(self):
        """Test that new user with no routes gets empty results."""
        # Create new user with no routes
        new_user = User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="testpass123",
            is_active=True,
        )
        new_token = Token.objects.create(user=new_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {new_token.key}")
        response = self.client.get(self.route_list_url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(len(response.data["results"]), 0)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_list_routes_only_get_method_allowed(self):
        """Test that only GET method is allowed for route list endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        # Note: POST is allowed for route creation, so we don't test it here
        # We only test methods that should NOT be allowed

        # Try PUT method
        response = self.client.put(self.route_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try DELETE method
        response = self.client.delete(self.route_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PATCH method
        response = self.client.patch(self.route_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


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
            priority=10,
        )
        self.tag2 = Tag.objects.create(
            name="Architecture",
            description="Architectural landmarks",
            is_active=True,
            priority=9,
        )
        self.tag3 = Tag.objects.create(
            name="Parks", description="Parks and nature", is_active=True, priority=8
        )
        self.tag_inactive = Tag.objects.create(
            name="Inactive Tag",
            description="This tag is inactive",
            is_active=False,
            priority=0,
        )

    # -------------------------------------------------------------------------
    # Manual Route Creation Tests
    # -------------------------------------------------------------------------

    def test_create_manual_route_with_name(self):
        """Test creating a manual route with custom name."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "manual", "name": "My Trip to Krakow"}

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

        data = {"route_type": "manual"}

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
            "name": "   ",  # Whitespace only
        }

        response = self.client.post(self.route_create_url, data, format="json")

        # Should succeed and use default name (service trims whitespace)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Custom Trip")

    def test_create_manual_route_with_tags_fails(self):
        """Test that manual routes cannot have tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "manual", "name": "My Trip", "tags": [self.tag1.id]}

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
            "description": "Some description",
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
            "name": "A" * 501,  # 501 characters
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

        data = {"route_type": "ai_generated", "tags": [self.tag1.id]}

        response = self.client.post(self.route_create_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "temporary")
        self.assertEqual(response.data["route_type"], "ai_generated")
        self.assertGreater(
            len(response.data["points"]), 0
        )  # Should have AI-generated points

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

        data = {"route_type": "ai_generated", "tags": [self.tag1.id, self.tag2.id]}

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
            "tags": [self.tag1.id, self.tag2.id, self.tag3.id],
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
            "description": "Interested in modern architecture and design",
        }

        response = self.client.post(self.route_create_url, data, format="json")

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify AI log contains description
        route = Route.objects.get(id=response.data["id"])
        ai_log = AIGenerationLog.objects.get(route=route)
        self.assertEqual(
            ai_log.additional_text_snapshot,
            "Interested in modern architecture and design",
        )

    def test_create_ai_route_without_tags_fails(self):
        """Test that AI-generated routes require tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "ai_generated"}

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)
        self.assertIn("wymagane", str(response.data["tags"][0]).lower())

    def test_create_ai_route_with_empty_tags_fails(self):
        """Test that AI-generated routes cannot have empty tags list."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "ai_generated", "tags": []}

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
            "tags": [self.tag1.id, self.tag2.id, self.tag3.id, tag4.id],
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
            "tags": [99999],  # Non-existent tag ID
        }

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

    def test_create_ai_route_with_inactive_tag_fails(self):
        """Test that inactive tags are rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "ai_generated", "tags": [self.tag_inactive.id]}

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
            "description": "A" * 1001,  # 1001 characters
        }

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_create_ai_route_generates_points(self):
        """Test that AI-generated routes have points created."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "ai_generated", "tags": [self.tag1.id, self.tag2.id]}

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

        data = {"route_type": "ai_generated", "tags": [self.tag1.id]}

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
        data = {"route_type": "manual", "name": "My Trip"}

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail authentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_route_without_route_type_fails(self):
        """Test that route_type is required."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"name": "My Trip"}

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route_type", response.data)

    def test_create_route_with_invalid_route_type_fails(self):
        """Test that invalid route_type is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "invalid_type"}

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route_type", response.data)

    def test_create_route_user_isolation(self):
        """Test that routes are created for the authenticated user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

        data = {"route_type": "manual", "name": "User 1 Trip"}

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
        data1 = {"route_type": "manual", "name": "Trip 1"}
        response1 = self.client.post(self.route_create_url, data1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create second route
        data2 = {"route_type": "ai_generated", "tags": [self.tag1.id]}
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
            "tags": [99999],  # Invalid tag ID
        }

        response = self.client.post(self.route_create_url, data, format="json")

        # Should fail
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify no partial data was created
        self.assertEqual(Route.objects.count(), initial_route_count)
        self.assertEqual(RouteTag.objects.count(), initial_tag_count)
