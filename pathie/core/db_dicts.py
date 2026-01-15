"""
Type definitions for Pathie core entities.

This file serves as the source of truth for data structures used throughout the application,
mirroring the database schema defined in DB Plan.
These TypedDicts should be used for type hinting when dealing with dictionaries,
serialized data, or values returned by `QuerySet.values()`.
"""

from datetime import datetime
from decimal import Decimal
from typing import TypedDict, Optional, List, Dict, Any, Literal

# Enums (Literal types for strict checking)
RouteStatus = Literal["temporary", "saved"]
RouteType = Literal["ai_generated", "manual"]
RoutePointSource = Literal["ai_generated", "manual"]
RatingType = Literal["place_description", "route"]


class RouteDict(TypedDict):
    """Represents a Route entity."""

    id: int
    user_id: int
    name: str
    status: RouteStatus
    route_type: RouteType
    saved_at: Optional[datetime]
    cached_at: Optional[datetime]
    cache_expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PlaceDict(TypedDict):
    """Represents a Place entity."""

    id: int
    name: str
    osm_id: Optional[int]
    wikipedia_id: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    lat: float
    lon: float
    data: Optional[Dict[str, Any]]  # JSONB
    created_at: datetime
    updated_at: datetime


class RoutePointDict(TypedDict):
    """Represents a RoutePoint entity (join table between Route and Place)."""

    id: int
    route_id: int
    place_id: int
    source: RoutePointSource
    position: int
    optimized_position: Optional[int]
    is_removed: bool
    added_at: datetime
    created_at: datetime
    updated_at: datetime


class PlaceDescriptionDict(TypedDict):
    """Represents a PlaceDescription entity."""

    id: int
    route_point_id: int
    language_code: str
    content: str
    created_at: datetime
    updated_at: datetime


class TagDict(TypedDict):
    """Represents a Tag entity."""

    id: int
    name: str
    description: Optional[str]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class RatingDict(TypedDict):
    """Represents a Rating entity."""

    id: int
    user_id: int
    rating_type: RatingType
    rating_value: int  # 1 or -1
    route_id: Optional[int]
    place_description_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class AIGenerationLogDict(TypedDict):
    """Represents an AIGenerationLog entity."""

    id: int
    route_id: int
    model: str
    provider: Optional[str]
    prompt_hash: Optional[str]
    tags_snapshot: List[str]
    additional_text_snapshot: Optional[str]
    points_count: Optional[int]
    tokens_prompt: Optional[int]
    tokens_completion: Optional[int]
    cost_usd: Optional[Decimal]
    request_id: Optional[str]
    metadata: Optional[Dict[str, Any]]  # JSONB
    created_at: datetime
