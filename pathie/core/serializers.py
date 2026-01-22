from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Route, RoutePoint, Place, PlaceDescription, Tag, Rating, RouteTag

User = get_user_model()


# -----------------------------------------------------------------------------
# Authentication Serializers
# -----------------------------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication via email and password.
    Validates credentials and returns the authenticated user instance.
    """

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Adres e-mail jest wymagany.",
            "invalid": "Wprowadź prawidłowy adres e-mail.",
        },
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        error_messages={"required": "Hasło jest wymagane."},
    )

    def validate(self, attrs: dict) -> dict:
        """
        Validates user credentials.

        Args:
            attrs: Dictionary containing email and password

        Returns:
            Dictionary with validated data including user instance

        Raises:
            serializers.ValidationError: If credentials are invalid
        """
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError(
                "Adres e-mail i hasło są wymagane.", code="missing_fields"
            )

        # Normalize email to lowercase for case-insensitive lookup
        email = email.lower()

        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Nieprawidłowy adres e-mail lub hasło.", code="invalid_credentials"
            )

        # Check password
        if not user.check_password(password):
            raise serializers.ValidationError(
                "Nieprawidłowy adres e-mail lub hasło.", code="invalid_credentials"
            )

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError(
                "To konto zostało dezaktywowane.", code="account_inactive"
            )

        # Add user instance to validated data
        attrs["user"] = user
        return attrs


# -----------------------------------------------------------------------------
# Tag Serializers
# -----------------------------------------------------------------------------


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag model.
    Read-only for standard API usage.
    """

    class Meta:
        model = Tag
        fields = ["id", "name", "description", "is_active"]
        read_only_fields = ["id", "name", "description", "is_active"]


# -----------------------------------------------------------------------------
# Place & Description Serializers (Nested DTOs)
# -----------------------------------------------------------------------------


class PlaceSerializer(serializers.ModelSerializer):
    """
    Serializer for Place model.
    Used as nested representation in Route Points.
    """

    class Meta:
        model = Place
        fields = [
            "id",
            "name",
            "osm_id",
            "wikipedia_id",
            "address",
            "city",
            "country",
            "lat",
            "lon",
            "data",
        ]


class PlaceDescriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for PlaceDescription model.
    Used as nested content for Route Points.
    """

    class Meta:
        model = PlaceDescription
        fields = ["id", "content", "language_code"]


# -----------------------------------------------------------------------------
# Route Point Serializers
# -----------------------------------------------------------------------------


class RoutePointSerializer(serializers.ModelSerializer):
    """
    DTO for RoutePoint.
    Includes nested Place and Description.
    """

    place = PlaceSerializer(read_only=True)
    description = PlaceDescriptionSerializer(
        read_only=True
    )  # related_name='description' on model

    class Meta:
        model = RoutePoint
        fields = ["id", "position", "place", "description"]


class PlaceInputSerializer(serializers.Serializer):
    """
    Input serializer for creating a Place within a RoutePoint.
    """

    name = serializers.CharField(max_length=255)
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    osm_id = serializers.IntegerField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)


class RoutePointCreateSerializer(serializers.ModelSerializer):
    """
    Command Model for adding a point to a manual route.
    Handles nested Place creation/lookup.
    """

    place = PlaceInputSerializer(write_only=True)

    class Meta:
        model = RoutePoint
        fields = ["place"]

    def create(self, validated_data):
        place_data = validated_data.pop("place")

        # Simple get_or_create logic based on osm_id if present
        osm_id = place_data.get("osm_id")
        place = None

        if osm_id:
            place = Place.objects.filter(osm_id=osm_id).first()

        if not place:
            place = Place.objects.create(**place_data)

        # route_id is provided by the view logic (injected into validated_data or passed via save)
        route = validated_data.get("route")
        if not route:
            # Fallback if route is not in validated_data, check context
            # (In a real view, perform_create would pass route=...)
            raise serializers.ValidationError("Route context required.")

        # Calculate next position
        last_position = (
            RoutePoint.objects.filter(route=route)
            .order_by("-position")
            .values_list("position", flat=True)
            .first()
        )
        position = (last_position or 0) + 1

        route_point = RoutePoint.objects.create(
            route=route, place=place, position=position, source="manual"
        )
        return route_point


# -----------------------------------------------------------------------------
# Route Serializers
# -----------------------------------------------------------------------------


class RouteListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for Route list view.
    """

    points_count = serializers.IntegerField(read_only=True)  # Annotated in QuerySet

    class Meta:
        model = Route
        fields = ["id", "name", "status", "route_type", "created_at", "points_count"]
        read_only_fields = ["id", "created_at", "points_count"]


class RouteDetailSerializer(serializers.ModelSerializer):
    """
    Full Route DTO including nested points.
    """

    points = RoutePointSerializer(
        source="points", many=True, read_only=True
    )  # related_name='points'
    user_rating_value = serializers.IntegerField(
        read_only=True, allow_null=True
    )  # Annotated

    class Meta:
        model = Route
        fields = ["id", "name", "status", "route_type", "user_rating_value", "points"]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "points",
            "user_rating_value",
        ]


class RouteCreateSerializer(serializers.ModelSerializer):
    """
    Command Model for creating a Route.
    Handles 'ai_generated' vs 'manual' validation logic and Tag association.
    """

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False
    )
    description = serializers.CharField(
        write_only=True, required=False, max_length=10000
    )

    class Meta:
        model = Route
        fields = ["route_type", "tags", "description", "name"]

    def validate(self, data):
        route_type = data.get("route_type")

        if route_type == "ai_generated":
            tags = data.get("tags", [])
            if not tags:
                raise serializers.ValidationError(
                    {"tags": "Tags are required for AI generated routes."}
                )
            if len(tags) > 3:
                raise serializers.ValidationError({"tags": "Maximum 3 tags allowed."})
            if len(tags) < 1:
                raise serializers.ValidationError(
                    {"tags": "At least 1 tag is required."}
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        # Description is currently not stored on Route model (maybe used for AI generation trigger)
        # If needed for AI Service, it should be handled there.
        # We pop it so it doesn't cause error on Route.objects.create
        _ = validated_data.pop("description", None)

        # User should be passed in serializer.save(user=request.user)
        route = Route.objects.create(**validated_data)

        if tags:
            route_tags = [RouteTag(route=route, tag=tag) for tag in tags]
            RouteTag.objects.bulk_create(route_tags)

        return route


class RouteUpdateSerializer(serializers.ModelSerializer):
    """
    Command Model for updating Route status/name.
    """

    class Meta:
        model = Route
        fields = ["name", "status"]

    def validate_status(self, value):
        if value not in ["temporary", "saved"]:
            raise serializers.ValidationError("Invalid status.")
        return value


class RouteOptimizeSerializer(serializers.Serializer):
    """
    Trigger serializer for route optimization.
    Currently empty as configuration is optional/TBD.
    """

    pass


# -----------------------------------------------------------------------------
# Rating Serializers
# -----------------------------------------------------------------------------


class RatingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Ratings.
    """

    class Meta:
        model = Rating
        fields = ["id", "rating_type", "rating_value", "route", "place_description"]
        read_only_fields = ["id"]

    def validate(self, data):
        rating_type = data.get("rating_type")
        route = data.get("route")
        place_description = data.get("place_description")

        if rating_type == "route":
            if not route:
                raise serializers.ValidationError(
                    {"route": "Route ID is required for route rating."}
                )
            # Ensure place_description is not set
            if place_description:
                raise serializers.ValidationError(
                    {"place_description": "Should be null for route rating."}
                )

        if rating_type == "place_description":
            if not place_description:
                raise serializers.ValidationError(
                    {
                        "place_description": "Place Description ID is required for description rating."
                    }
                )
            # Ensure route is not set
            if route:
                raise serializers.ValidationError(
                    {"route": "Should be null for place_description rating."}
                )

        if data.get("rating_value") not in [1, -1]:
            raise serializers.ValidationError(
                {"rating_value": "Rating must be 1 (like) or -1 (dislike)."}
            )

        return data
