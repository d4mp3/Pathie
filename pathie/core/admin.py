"""Django admin configuration for core models."""
from django.contrib import admin

from .models import (
    AIGenerationLog,
    Place,
    PlaceDescription,
    Rating,
    Route,
    RoutePoint,
    RouteTag,
    Tag,
)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    """Admin for Route model."""
    
    list_display = ['name', 'user', 'status', 'route_type', 'created_at']
    list_filter = ['status', 'route_type', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    """Admin for Place model."""
    
    list_display = ['name', 'city', 'country', 'lat', 'lon', 'created_at']
    search_fields = ['name', 'address', 'city', 'country']
    list_filter = ['country', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RoutePoint)
class RoutePointAdmin(admin.ModelAdmin):
    """Admin for RoutePoint model."""
    
    list_display = ['route', 'place', 'position', 'source', 'is_removed', 'created_at']
    list_filter = ['source', 'is_removed', 'created_at']
    search_fields = ['route__name', 'place__name']
    readonly_fields = ['added_at', 'created_at', 'updated_at']


@admin.register(PlaceDescription)
class PlaceDescriptionAdmin(admin.ModelAdmin):
    """Admin for PlaceDescription model."""
    
    list_display = ['route_point', 'language_code', 'created_at']
    list_filter = ['language_code', 'created_at']
    search_fields = ['route_point__place__name', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model."""
    
    list_display = ['name', 'is_active', 'priority', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RouteTag)
class RouteTagAdmin(admin.ModelAdmin):
    """Admin for RouteTag model."""
    
    list_display = ['route', 'tag', 'created_at']
    list_filter = ['created_at']
    search_fields = ['route__name', 'tag__name']
    readonly_fields = ['created_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin for Rating model."""
    
    list_display = ['user', 'rating_type', 'rating_value', 'created_at']
    list_filter = ['rating_type', 'rating_value', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AIGenerationLog)
class AIGenerationLogAdmin(admin.ModelAdmin):
    """Admin for AIGenerationLog model."""
    
    list_display = ['route', 'model', 'provider', 'points_count', 'cost_usd', 'created_at']
    list_filter = ['model', 'provider', 'created_at']
    search_fields = ['route__name', 'model', 'provider']
    readonly_fields = ['created_at']
