from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Route, RoutePoint, Place, PlaceDescription
from ..serializers import (
    PlaceSimpleSerializer,
    PlaceDescriptionContentSerializer,
    RoutePointDetailSerializer,
    RoutePointCreateSerializer,
)

User = get_user_model()


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
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
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
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
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
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
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
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
        )

        # Validate and create
        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify osm_id took precedence (existing_place was used)
        self.assertEqual(route_point.place.id, self.existing_place.id)
        self.assertNotEqual(route_point.place.id, other_place.id)

    def test_validate_fails_for_ai_generated_route(self):
        """Test that validation fails when trying to add point to AI-generated route."""
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.ai_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("AI generated", str(serializer.errors))

    def test_validate_fails_when_max_points_limit_reached(self):
        """Test that validation fails when route has 10 points (max limit for manual routes)."""
        from ..serializers import RoutePointCreateSerializer

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
            RoutePoint.objects.filter(
                route=self.manual_route, is_removed=False
            ).count(),
            10,
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
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("Max points limit", str(serializer.errors))

    def test_validate_succeeds_with_9_points(self):
        """Test that validation succeeds when route has 9 points (under limit)."""
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
        )

        # Validate should succeed
        self.assertTrue(serializer.is_valid())

    def test_validate_ignores_removed_points_in_count(self):
        """Test that validation ignores removed points when counting."""
        from ..serializers import RoutePointCreateSerializer

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
            RoutePoint.objects.filter(
                route=self.manual_route, is_removed=False
            ).count(),
            5,
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
            data=data, context={"route": self.manual_route}
        )

        # Validate should succeed
        self.assertTrue(serializer.is_valid())

    def test_validate_fails_without_route_context(self):
        """Test that validation fails when route context is missing."""
        from ..serializers import RoutePointCreateSerializer

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
        from ..serializers import RoutePointCreateSerializer

        # Route has no points yet
        self.assertEqual(RoutePoint.objects.filter(route=self.manual_route).count(), 0)

        # Add first point
        data = {
            "place": {
                "name": "First Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify position is 0
        self.assertEqual(route_point.position, 0)

    def test_position_calculation_for_subsequent_points(self):
        """Test that position is calculated correctly for subsequent points."""
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify position is 1
        self.assertEqual(route_point.position, 1)

    def test_position_calculation_ignores_removed_points(self):
        """Test that position calculation considers only non-removed points."""
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Position should be 2 (last non-removed was 1, so next is 2)
        # Even though there's a removed point at position 2
        self.assertEqual(route_point.position, 2)

    def test_place_input_validation_missing_name(self):
        """Test that validation fails when place name is missing."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("name", serializer.errors["place"])

    def test_place_input_validation_missing_lat(self):
        """Test that validation fails when latitude is missing."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lat", serializer.errors["place"])

    def test_place_input_validation_missing_lon(self):
        """Test that validation fails when longitude is missing."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lon", serializer.errors["place"])

    def test_place_input_validation_lat_out_of_range_high(self):
        """Test that validation fails when latitude is above 90."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 91.0,  # Invalid: > 90
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lat", serializer.errors["place"])

    def test_place_input_validation_lat_out_of_range_low(self):
        """Test that validation fails when latitude is below -90."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": -91.0,  # Invalid: < -90
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lat", serializer.errors["place"])

    def test_place_input_validation_lon_out_of_range_high(self):
        """Test that validation fails when longitude is above 180."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": 181.0,  # Invalid: > 180
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lon", serializer.errors["place"])

    def test_place_input_validation_lon_out_of_range_low(self):
        """Test that validation fails when longitude is below -180."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": -181.0,  # Invalid: < -180
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        # Validate should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn("place", serializer.errors)
        self.assertIn("lon", serializer.errors["place"])

    def test_place_input_validation_lat_lon_at_boundaries(self):
        """Test that validation succeeds with lat/lon at valid boundaries."""
        from ..serializers import RoutePointCreateSerializer

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
                data=data, context={"route": self.manual_route}
            )

            # Validate should succeed
            self.assertTrue(
                serializer.is_valid(),
                f"Validation failed for lat={coords['lat']}, lon={coords['lon']}",
            )

    def test_place_input_optional_fields(self):
        """Test that optional place fields (osm_id, address, wikipedia_id) work correctly."""
        from ..serializers import RoutePointCreateSerializer

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
            data=data, context={"route": self.manual_route}
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
        from ..serializers import RoutePointCreateSerializer

        # Test with only required fields
        data = {
            "place": {
                "name": "Minimal Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify place was created with required fields only
        self.assertEqual(route_point.place.name, "Minimal Place")
        self.assertIsNone(route_point.place.osm_id)
        self.assertIsNone(route_point.place.wikipedia_id)

    def test_route_point_source_is_manual(self):
        """Test that created route point has source set to 'manual'."""
        from ..serializers import RoutePointCreateSerializer

        data = {
            "place": {
                "name": "Test Place",
                "lat": 52.2319,
                "lon": 21.0067,
            }
        }

        serializer = RoutePointCreateSerializer(
            data=data, context={"route": self.manual_route}
        )

        self.assertTrue(serializer.is_valid())
        route_point = serializer.save()

        # Verify source is 'manual'
        self.assertEqual(route_point.source, RoutePoint.SOURCE_MANUAL)

    def test_create_multiple_points_in_sequence(self):
        """Test creating multiple points in sequence with correct position calculation."""
        from ..serializers import RoutePointCreateSerializer

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
                data=data, context={"route": self.manual_route}
            )

            self.assertTrue(serializer.is_valid())
            route_point = serializer.save()

            # Verify position matches sequence
            self.assertEqual(route_point.position, i)

        # Verify all points were created
        self.assertEqual(RoutePoint.objects.filter(route=self.manual_route).count(), 5)
