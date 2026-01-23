"""
Business logic services for the core app.

This module contains service layer functions that encapsulate complex business logic,
keeping views thin and focused on HTTP concerns.
"""

import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Route, RoutePoint, Place, Tag, RouteTag, AIGenerationLog

User = get_user_model()
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
    def create_route(user: User, validated_data: Dict[str, Any]) -> Route:
        """
        Create a new route based on route_type (ai_generated or manual).
        
        This is the main entry point for route creation, delegating to specific
        methods based on the route type.
        
        Args:
            user: User creating the route
            validated_data: Dictionary with validated data from serializer
                - route_type: 'ai_generated' or 'manual'
                - tags: List of Tag objects (for AI generated)
                - description: Optional description (for AI generated)
                - name: Optional name (for manual)
                
        Returns:
            Created Route instance with all related data
            
        Raises:
            BusinessLogicException: If route creation fails
            ValidationError: If data validation fails
            
        Example:
            >>> route = RouteService.create_route(
            ...     user=request.user,
            ...     validated_data={
            ...         'route_type': 'ai_generated',
            ...         'tags': [tag1, tag2],
            ...         'description': 'Museums in Warsaw'
            ...     }
            ... )
        """
        route_type = validated_data.get('route_type')
        
        logger.info(
            f"Creating route: user_id={user.id}, route_type={route_type}"
        )
        
        if route_type == Route.TYPE_AI_GENERATED:
            return RouteService._create_ai_route(user, validated_data)
        elif route_type == Route.TYPE_MANUAL:
            return RouteService._create_manual_route(user, validated_data)
        else:
            raise BusinessLogicException(
                f"Nieobsługiwany typ trasy: {route_type}"
            )

    @staticmethod
    @transaction.atomic
    def _create_manual_route(user: User, data: Dict[str, Any]) -> Route:
        """
        Create an empty manual route for user to add points manually.
        
        Creates a route with:
        - Status: temporary (user needs to save it later)
        - Type: manual
        - Name: User-provided or default "My Custom Trip"
        - No points initially
        
        Args:
            user: User creating the route
            data: Dictionary with validated data
                - name: Optional route name
                
        Returns:
            Created Route instance
            
        Example:
            >>> route = RouteService._create_manual_route(
            ...     user=request.user,
            ...     data={'name': 'Trip to Krakow'}
            ... )
        """
        name = data.get('name', '').strip()
        if not name:
            name = "My Custom Trip"
        
        logger.info(
            f"Creating manual route: user_id={user.id}, name={name}"
        )
        
        try:
            route = Route.objects.create(
                user=user,
                name=name,
                status=Route.STATUS_TEMPORARY,
                route_type=Route.TYPE_MANUAL
            )
            
            logger.info(
                f"Successfully created manual route: route_id={route.id}, "
                f"user_id={user.id}"
            )
            
            return route
            
        except Exception as e:
            logger.error(
                f"Error creating manual route: user_id={user.id}, error={str(e)}",
                exc_info=True
            )
            raise

    @staticmethod
    @transaction.atomic
    def _create_ai_route(user: User, data: Dict[str, Any]) -> Route:
        """
        Create an AI-generated route with points and descriptions.
        
        This method orchestrates the AI generation process:
        1. Creates Route object with temporary status
        2. Associates tags with the route
        3. Creates AIGenerationLog entry
        4. Calls AI service to generate route points (SYNCHRONOUS in MVP)
        5. Creates Place, RoutePoint, and PlaceDescription records
        6. Updates AIGenerationLog with results
        
        Args:
            user: User creating the route
            data: Dictionary with validated data
                - tags: List of Tag objects (1-3 tags)
                - description: Optional additional context for AI
                
        Returns:
            Created Route instance with all points and descriptions
            
        Raises:
            BusinessLogicException: If AI generation fails
            
        Example:
            >>> route = RouteService._create_ai_route(
            ...     user=request.user,
            ...     data={
            ...         'tags': [tag1, tag2],
            ...         'description': 'Interested in modern architecture'
            ...     }
            ... )
        """
        tags = data.get('tags', [])
        description = data.get('description', '').strip()
        
        logger.info(
            f"Creating AI-generated route: user_id={user.id}, "
            f"tags={[tag.id for tag in tags]}, "
            f"description_length={len(description)}"
        )
        
        try:
            # Step 1: Create Route object with temporary status
            # Generate a temporary name based on tags
            tag_names = [tag.name for tag in tags]
            route_name = f"{', '.join(tag_names[:2])} Route"
            if len(tag_names) > 2:
                route_name = f"{tag_names[0]} & More Route"
            
            route = Route.objects.create(
                user=user,
                name=route_name,
                status=Route.STATUS_TEMPORARY,
                route_type=Route.TYPE_AI_GENERATED
            )
            
            logger.info(f"Created route object: route_id={route.id}")
            
            # Step 2: Associate tags with route
            route_tags = [RouteTag(route=route, tag=tag) for tag in tags]
            RouteTag.objects.bulk_create(route_tags)
            
            logger.info(
                f"Associated {len(tags)} tags with route: route_id={route.id}"
            )
            
            # Step 3: Create AIGenerationLog entry
            ai_log = AIGenerationLog.objects.create(
                route=route,
                model="mock-model-v1",  # Will be replaced with real model name
                provider="mock",  # Will be replaced with real provider
                tags_snapshot=[tag.name for tag in tags],
                additional_text_snapshot=description if description else None
            )
            
            logger.info(
                f"Created AI generation log: log_id={ai_log.id}, route_id={route.id}"
            )
            
            # Step 4: Call AI service to generate route points
            # TODO: Replace with real AI service call
            # For now, we'll use a mock implementation
            generated_points = RouteService._mock_ai_generation(tags, description)
            
            logger.info(
                f"AI generated {len(generated_points)} points for route_id={route.id}"
            )
            
            # Step 5: Create Place, RoutePoint, and PlaceDescription records
            RouteService._create_route_points_from_ai(route, generated_points)
            
            # Step 6: Update AIGenerationLog with results
            ai_log.points_count = len(generated_points)
            ai_log.save(update_fields=['points_count'])
            
            logger.info(
                f"Successfully created AI-generated route: route_id={route.id}, "
                f"points_count={len(generated_points)}"
            )
            
            return route
            
        except Exception as e:
            logger.error(
                f"Error creating AI-generated route: user_id={user.id}, "
                f"error={str(e)}",
                exc_info=True
            )
            # Transaction will be rolled back automatically
            raise BusinessLogicException(
                "Nie udało się wygenerować trasy. Spróbuj ponownie później."
            )

    @staticmethod
    def _mock_ai_generation(
        tags: List[Tag],
        description: str
    ) -> List[Dict[str, Any]]:
        """
        Mock AI generation service for testing.
        
        Returns hardcoded test data that simulates AI-generated route points.
        This will be replaced with real AI service integration.
        
        Args:
            tags: List of Tag objects for route theme
            description: Additional context from user
            
        Returns:
            List of dictionaries with place data:
            [
                {
                    'name': 'Place Name',
                    'lat': 52.2297,
                    'lon': 21.0122,
                    'address': 'Street Address',
                    'city': 'City',
                    'country': 'Country',
                    'osm_id': 'optional_osm_id',
                    'wikipedia_id': 'optional_wiki_id',
                    'description': 'AI-generated description of the place'
                },
                ...
            ]
        """
        logger.info(
            f"Mock AI generation called with tags={[t.name for t in tags]}, "
            f"description={description[:50] if description else 'None'}"
        )
        
        # Mock data - will be replaced with real AI service
        return [
            {
                'name': 'Palace of Culture and Science',
                'lat': 52.2319,
                'lon': 21.0067,
                'address': 'plac Defilad 1',
                'city': 'Warsaw',
                'country': 'Poland',
                'osm_id': 'N123456',
                'wikipedia_id': None,
                'description': 'A notable landmark in Warsaw, offering panoramic views of the city.'
            },
            {
                'name': 'Royal Castle',
                'lat': 52.2480,
                'lon': 21.0514,
                'address': 'plac Zamkowy 4',
                'city': 'Warsaw',
                'country': 'Poland',
                'osm_id': 'N789012',
                'wikipedia_id': None,
                'description': 'Historic royal residence with beautiful architecture and rich history.'
            },
            {
                'name': 'Łazienki Park',
                'lat': 52.2156,
                'lon': 21.0352,
                'address': 'Agrykoli 1',
                'city': 'Warsaw',
                'country': 'Poland',
                'osm_id': None,
                'wikipedia_id': 'Q654321',
                'description': 'Beautiful park with palace, peacocks, and Chopin monument.'
            }
        ]

    @staticmethod
    def _create_route_points_from_ai(
        route: Route,
        generated_points: List[Dict[str, Any]]
    ) -> None:
        """
        Create Place, RoutePoint, and PlaceDescription records from AI output.
        
        For each generated point:
        1. Check if Place exists (by osm_id or wikipedia_id)
        2. Create Place if it doesn't exist
        3. Create RoutePoint linking Route and Place
        4. Create PlaceDescription with AI-generated content
        
        Args:
            route: Route instance to add points to
            generated_points: List of dictionaries with place data from AI
            
        Raises:
            Exception: If database operations fail
        """
        from .models import PlaceDescription  # Import here to avoid circular import
        
        logger.info(
            f"Creating {len(generated_points)} route points for route_id={route.id}"
        )
        
        for position, point_data in enumerate(generated_points):
            try:
                # Extract data
                description_text = point_data.pop('description', '')
                osm_id = point_data.get('osm_id')
                wikipedia_id = point_data.get('wikipedia_id')
                
                # Step 1 & 2: Find or create Place
                place = None
                
                # Try to find by osm_id first
                if osm_id:
                    place = Place.objects.filter(osm_id=osm_id).first()
                
                # Try wikipedia_id if not found
                if not place and wikipedia_id:
                    place = Place.objects.filter(wikipedia_id=wikipedia_id).first()
                
                # Create new place if not found
                if not place:
                    place = Place.objects.create(**point_data)
                    logger.info(
                        f"Created new place: place_id={place.id}, name={place.name}"
                    )
                else:
                    logger.info(
                        f"Using existing place: place_id={place.id}, name={place.name}"
                    )
                
                # Step 3: Create RoutePoint
                route_point = RoutePoint.objects.create(
                    route=route,
                    place=place,
                    position=position,
                    source=RoutePoint.SOURCE_AI_GENERATED
                )
                
                logger.info(
                    f"Created route point: point_id={route_point.id}, "
                    f"position={position}, place_id={place.id}"
                )
                
                # Step 4: Create PlaceDescription if we have description text
                if description_text:
                    PlaceDescription.objects.create(
                        route_point=route_point,
                        content=description_text,
                        language_code='pl'  # Default to Polish
                    )
                    logger.info(
                        f"Created place description for route_point_id={route_point.id}"
                    )
                
            except Exception as e:
                logger.error(
                    f"Error creating route point at position {position}: {str(e)}",
                    exc_info=True
                )
                raise

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
