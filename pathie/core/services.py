"""
Business logic services for the core app.

This module contains service layer functions that encapsulate complex business logic,
keeping views thin and focused on HTTP concerns.
"""

import logging
from typing import List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Route, RoutePoint, Place

logger = logging.getLogger(__name__)


class BusinessLogicException(Exception):
    """
    Custom exception for business logic violations.
    Used to distinguish business rule errors from technical errors.
    """
    pass


class RouteService:
    """
    Service class for Route-related business logic.
    """

    @staticmethod
    @transaction.atomic
    def update_route(route: Route, validated_data: Dict[str, Any]) -> Route:
        """
        Update route name and/or status.
        
        When status changes to 'saved', automatically sets saved_at timestamp.
        This is the primary method for persisting temporary routes.
        
        Args:
            route: Route instance to update
            validated_data: Dictionary with validated fields (name, status)
            
        Returns:
            Updated Route instance
            
        Raises:
            ValidationError: If validation fails
            
        Example:
            >>> route = Route.objects.get(id=123)
            >>> updated_route = RouteService.update_route(
            ...     route,
            ...     {'name': 'My Trip', 'status': 'saved'}
            ... )
        """
        logger.info(
            f"Updating route: route_id={route.id}, "
            f"current_status={route.status}, "
            f"update_data={validated_data}"
        )
        
        # Track if status is changing to 'saved'
        status_changing_to_saved = False
        new_status = validated_data.get('status')
        
        if new_status and new_status != route.status:
            logger.info(
                f"Status change detected: route_id={route.id}, "
                f"old_status={route.status}, new_status={new_status}"
            )
            
            if new_status == Route.STATUS_SAVED and route.status != Route.STATUS_SAVED:
                status_changing_to_saved = True
        
        # Update fields from validated_data
        for field, value in validated_data.items():
            setattr(route, field, value)
        
        # Set saved_at timestamp if status is changing to 'saved'
        if status_changing_to_saved:
            route.saved_at = timezone.now()
            logger.info(
                f"Setting saved_at timestamp: route_id={route.id}, "
                f"saved_at={route.saved_at}"
            )
        
        # Save the route
        try:
            route.full_clean()  # Validate model constraints
            route.save()
            logger.info(f"Successfully updated route: route_id={route.id}")
        except ValidationError as e:
            logger.error(
                f"Validation error during route update: route_id={route.id}, "
                f"error={str(e)}",
                exc_info=True
            )
            raise
        
        return route

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate approximate distance between two points using Haversine formula.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2

        # Earth radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    @staticmethod
    def _nearest_neighbor_tsp(points: List[RoutePoint]) -> List[RoutePoint]:
        """
        Simple nearest neighbor algorithm for TSP approximation.

        Starts from the first point and always moves to the nearest unvisited point.
        This is a greedy approximation that works well for small sets.

        Args:
            points: List of RoutePoint objects to optimize

        Returns:
            List of RoutePoint objects in optimized order
        """
        if len(points) <= 1:
            return points

        # Start with the first point (assumed to be the starting location)
        optimized = [points[0]]
        remaining = points[1:]

        while remaining:
            current_point = optimized[-1]
            current_place = current_point.place

            # Find nearest unvisited point
            nearest = min(
                remaining,
                key=lambda p: RouteService._calculate_distance(
                    current_place.lat,
                    current_place.lon,
                    p.place.lat,
                    p.place.lon
                )
            )

            optimized.append(nearest)
            remaining.remove(nearest)

        return optimized

    @staticmethod
    @transaction.atomic
    def optimize_route(route: Route, config: Dict[str, Any] = None) -> List[RoutePoint]:
        """
        Optimize the order of points in a route to find the shortest path.

        This method:
        1. Validates that the route can be optimized (manual type, sufficient points)
        2. Retrieves all route points with related place data
        3. Applies optimization algorithm (nearest neighbor TSP)
        4. Updates the position field for all points in the database
        5. Returns the optimized list of points

        Args:
            route: Route instance to optimize
            config: Optional configuration dictionary (e.g., {'strategy': 'tsp_approx'})

        Returns:
            List of RoutePoint objects in optimized order

        Raises:
            BusinessLogicException: If route cannot be optimized (wrong type, too few points)

        Example:
            >>> route = Route.objects.get(id=123)
            >>> optimized_points = RouteService.optimize_route(route)
        """
        config = config or {}
        strategy = config.get('strategy', 'nearest_neighbor')

        logger.info(
            f"Starting route optimization for route_id={route.id}, "
            f"strategy={strategy}, route_type={route.route_type}"
        )

        # Business rule validation: Only manual routes can be optimized
        if route.route_type != Route.TYPE_MANUAL:
            logger.warning(
                f"Attempted to optimize non-manual route: route_id={route.id}, "
                f"route_type={route.route_type}"
            )
            raise BusinessLogicException(
                "Tylko trasy typu 'manual' mogą być optymalizowane."
            )

        # Fetch all points for the route with related place data
        points = list(
            RoutePoint.objects.filter(route=route, is_removed=False)
            .select_related('place')
            .order_by('position')
        )

        # Business rule validation: Need at least 2 points to optimize
        if len(points) < 2:
            logger.warning(
                f"Attempted to optimize route with insufficient points: "
                f"route_id={route.id}, points_count={len(points)}"
            )
            raise BusinessLogicException(
                "Trasa musi mieć co najmniej 2 punkty, aby można było ją optymalizować."
            )

        logger.info(f"Optimizing {len(points)} points for route_id={route.id}")

        try:
            # Apply optimization algorithm
            if strategy == 'nearest_neighbor' or strategy == 'tsp_approx':
                optimized_points = RouteService._nearest_neighbor_tsp(points)
            else:
                # Default to nearest neighbor
                logger.warning(f"Unknown strategy '{strategy}', using nearest_neighbor")
                optimized_points = RouteService._nearest_neighbor_tsp(points)

            # Update positions in database
            # To avoid unique constraint violations during update, we need to:
            # 1. First set all positions to temporary negative values
            # 2. Then set them to final values
            
            # Step 1: Set temporary negative positions to avoid conflicts
            for idx, point in enumerate(optimized_points):
                point.position = -(idx + 1)  # Negative values: -1, -2, -3, etc.
            
            RoutePoint.objects.bulk_update(optimized_points, ['position'])
            
            # Step 2: Set final positions
            for idx, point in enumerate(optimized_points):
                point.position = idx  # Final values: 0, 1, 2, etc.
            
            RoutePoint.objects.bulk_update(optimized_points, ['position'])

            logger.info(
                f"Successfully optimized route_id={route.id}, "
                f"updated {len(optimized_points)} points"
            )

            return optimized_points

        except Exception as e:
            logger.error(
                f"Error during route optimization: route_id={route.id}, error={str(e)}",
                exc_info=True
            )
            raise

    @staticmethod
    @transaction.atomic
    def soft_delete_point(route_point: RoutePoint) -> None:
        """
        Soft delete a route point by setting is_removed flag to True.
        
        This method marks a route point as removed without physically deleting it
        from the database. This preserves the associated PlaceDescription and
        AI-generated content while hiding the point from route queries.
        
        Args:
            route_point: RoutePoint instance to soft delete
            
        Raises:
            ValidationError: If the operation fails
            
        Example:
            >>> point = RoutePoint.objects.get(id=123)
            >>> RouteService.soft_delete_point(point)
        
        Notes:
            - Sets is_removed = True
            - Does not modify position or other fields
            - Frontend should filter by is_removed=False when displaying points
        """
        logger.info(
            f"Soft deleting route point: point_id={route_point.id}, "
            f"route_id={route_point.route.id}, place_id={route_point.place.id}"
        )
        
        # Set the is_removed flag
        route_point.is_removed = True
        
        try:
            # Save only the is_removed field for efficiency
            route_point.save(update_fields=['is_removed'])
            
            logger.info(
                f"Successfully soft deleted route point: point_id={route_point.id}"
            )
        except Exception as e:
            logger.error(
                f"Error during route point soft delete: "
                f"point_id={route_point.id}, error={str(e)}",
                exc_info=True
            )
            raise
