"""
Custom permission classes for the core app.

This module contains permission classes that extend Django REST Framework's
base permissions to implement custom authorization logic.
"""

from rest_framework import permissions
from typing import Any

from .models import Route, RoutePoint


class IsRouteOwner(permissions.BasePermission):
    """
    Permission class that checks if the authenticated user is the owner of the route.
    
    This permission is used to ensure that users can only access and modify
    their own routes and route points.
    
    Usage:
        - Can be applied to views that work with Route or RoutePoint objects
        - Automatically checks route ownership based on the object type
        - Returns 404 if permission is denied (standard DRF behavior)
    
    Examples:
        >>> class MyRouteView(APIView):
        ...     permission_classes = [IsAuthenticated, IsRouteOwner]
    """
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """
        Check if the user has permission to access the given object.
        
        Args:
            request: HTTP request object with authenticated user
            view: View that is being accessed
            obj: Object being accessed (Route or RoutePoint)
            
        Returns:
            True if user owns the route, False otherwise
            
        Notes:
            - For Route objects: checks if obj.user == request.user
            - For RoutePoint objects: checks if obj.route.user == request.user
            - For other objects: denies access (returns False)
        """
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check ownership based on object type
        if isinstance(obj, Route):
            return obj.user == request.user
        elif isinstance(obj, RoutePoint):
            return obj.route.user == request.user
        
        # For unknown object types, deny access
        return False
