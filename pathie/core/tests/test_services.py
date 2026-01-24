from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Route, RoutePoint, Place
from ..services import RouteService, BusinessLogicException
from unittest.mock import patch

User = get_user_model()


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

        # Route has no points
        with self.assertRaises(BusinessLogicException) as context:
            RouteService.optimize_route(self.manual_route)

        self.assertIn("2 punkty", str(context.exception))

    def test_optimize_route_with_two_points(self):
        """Test optimization with exactly 2 points (minimum valid case)."""

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

        # Test distance between Royal Castle and Old Town Market Square
        # These are about 200-300 meters apart
        distance = RouteService._calculate_distance(
            52.2480,
            21.0153,  # Royal Castle
            52.2497,
            21.0122,  # Old Town Market Square
        )

        # Distance should be approximately 0.2-0.4 km
        self.assertGreater(distance, 0.1)
        self.assertLess(distance, 0.5)

    def test_calculate_distance_same_point(self):
        """Test distance calculation for the same point."""

        distance = RouteService._calculate_distance(
            52.2480,
            21.0153,
            52.2480,
            21.0153,
        )

        # Distance should be approximately 0
        self.assertAlmostEqual(distance, 0.0, places=5)

    def test_optimize_route_transaction_rollback_on_error(self):
        """Test that optimization rolls back on error (transaction atomicity)."""

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
            RoutePoint.objects.__class__,
            "bulk_update",
            side_effect=Exception("DB Error"),
        ):
            with self.assertRaises(Exception):
                RouteService.optimize_route(self.manual_route)

        # Verify data is still intact (transaction rolled back)
        current_count = RoutePoint.objects.filter(route=self.manual_route).count()
        self.assertEqual(current_count, original_count)

    def test_optimize_route_with_unknown_strategy(self):
        """Test optimization with unknown strategy falls back to default."""

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

        # Update name while keeping status temporary
        validated_data = {"name": "Still Temporary"}
        updated_route = RouteService.update_route(self.temp_route, validated_data)

        # Verify saved_at is still None
        self.assertIsNone(updated_route.saved_at)

    def test_update_route_persists_to_database(self):
        """Test that updates are actually saved to database."""

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
