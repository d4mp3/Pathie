"""
PostgreSQL Row Level Security (RLS) Middleware

Sets the app.user_id session variable for authenticated users,
enabling RLS policies to filter data by ownership.
"""
from typing import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse


class PostgreSQLRLSMiddleware:
    """
    Middleware to set PostgreSQL session variable for RLS.
    
    For authenticated users, sets app.user_id to enable row-level security policies.
    This must be called after AuthenticationMiddleware.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Set app.user_id session variable for authenticated users.
        """
        if request.user.is_authenticated:
            with connection.cursor() as cursor:
                # Set session variable: third parameter 'true' makes it transaction-local
                cursor.execute(
                    "SELECT set_config('app.user_id', %s, true)",
                    [str(request.user.id)]
                )
        
        response = self.get_response(request)
        return response

