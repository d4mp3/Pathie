"""
Business logic layer for data retrieval (selectors).

Selectors encapsulate complex query logic and keep views clean.
They return QuerySets or filtered data for use in API views.
"""

from django.db.models import QuerySet, Count, Q
from django.contrib.auth import get_user_model
from typing import Optional

from .models import Route

User = get_user_model()


def route_list_selector(
    user: User,
    status_filter: Optional[str] = None,
    ordering: Optional[str] = None,
) -> QuerySet[Route]:
    """
    Retrieve a filtered and annotated queryset of routes for a specific user.

    This selector encapsulates the business logic for fetching user routes with:
    - User isolation (only routes belonging to the user)
    - Status filtering (temporary, saved)
    - Points count annotation (excluding removed points)
    - Custom ordering

    Args:
        user: The authenticated user whose routes should be retrieved
        status_filter: Optional status to filter by ('temporary', 'saved').
                      Defaults to 'saved' if None.
        ordering: Optional field name for ordering results.
                 Supports '-' prefix for descending order.
                 Defaults to '-created_at' if None.

    Returns:
        QuerySet[Route]: Filtered and annotated queryset of Route objects
                        with 'points_count' annotation

    Examples:
        >>> routes = route_list_selector(request.user, status_filter='saved')
        >>> for route in routes:
        ...     print(f"{route.name}: {route.points_count} points")

    Notes:
        - The points_count annotation only counts RoutePoints with is_removed=False
        - QuerySet is not evaluated, allowing for further filtering or pagination
        - Default ordering is by created_at descending (newest first)
    """
    # Start with base queryset filtered by user for data isolation
    queryset = Route.objects.filter(user=user)

    # Apply status filter (default to 'saved' if not specified or invalid)
    valid_statuses = [Route.STATUS_TEMPORARY, Route.STATUS_SAVED]
    
    if status_filter is None or status_filter not in valid_statuses:
        status_filter = Route.STATUS_SAVED
    
    queryset = queryset.filter(status=status_filter)

    # Annotate with points count (excluding removed points)
    # This prevents N+1 queries and calculates count at database level
    queryset = queryset.annotate(
        points_count=Count(
            'points',
            filter=Q(points__is_removed=False)
        )
    )

    # Apply ordering (default to newest first)
    if ordering is None:
        ordering = '-created_at'

    # Validate ordering field to prevent SQL injection
    valid_ordering_fields = [
        'created_at', '-created_at',
        'name', '-name',
        'status', '-status',
        'route_type', '-route_type',
        'points_count', '-points_count',
    ]

    if ordering in valid_ordering_fields:
        queryset = queryset.order_by(ordering)
    else:
        # Fallback to default if invalid ordering field provided
        queryset = queryset.order_by('-created_at')

    return queryset
