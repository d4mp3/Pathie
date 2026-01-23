from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.authtoken.models import Token
from .models import Route, RoutePoint, Place, PlaceDescription, Tag, Rating, RouteTag

User = get_user_model()


# -----------------------------------------------------------------------------
# Authentication Serializers
# -----------------------------------------------------------------------------


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Returns basic user information for authentication responses.
    """

    user_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = User
        fields = ["user_id", "email"]
        read_only_fields = ["user_id", "email"]


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Validates email uniqueness, password strength, and password confirmation match.
    Creates new user and returns authentication token.
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
    password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        error_messages={"required": "Potwierdzenie hasła jest wymagane."},
    )

    def validate_email(self, value: str) -> str:
        """
        Validates email uniqueness.

        Args:
            value: Email address to validate

        Returns:
            Normalized (lowercase) email address

        Raises:
            serializers.ValidationError: If email already exists
        """
        # Normalize email to lowercase for case-insensitive lookup
        email = value.lower()

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "Użytkownik z tym adresem email już istnieje.", code="email_exists"
            )

        return email

    def validate_password(self, value: str) -> str:
        """
        Validates password strength using Django's password validators.

        Args:
            value: Password to validate

        Returns:
            Validated password

        Raises:
            serializers.ValidationError: If password doesn't meet requirements
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages), code="password_invalid")

        return value

    def validate(self, attrs: dict) -> dict:
        """
        Validates that password and password_confirm match.

        Args:
            attrs: Dictionary containing all input data

        Returns:
            Validated data

        Raises:
            serializers.ValidationError: If passwords don't match
        """
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Hasła nie są identyczne."},
                code="passwords_mismatch",
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> User:
        """
        Creates a new user with the validated data.

        Args:
            validated_data: Dictionary with validated email and password

        Returns:
            Created User instance with authentication token

        Note:
            - Username is set to email address
            - Password is automatically hashed by create_user
            - Authentication token is created automatically
        """
        email = validated_data["email"]
        password = validated_data["password"]

        # Create user with email as username
        user = User.objects.create_user(
            username=email, email=email, password=password
        )

        # Create authentication token for immediate API access
        Token.objects.create(user=user)

        return user


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


class PlaceSimpleSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for Place model.
    Used in route detail view for minimal place information.
    """

    class Meta:
        model = Place
        fields = ["id", "name", "lat", "lon", "address"]
        read_only_fields = ["id", "name", "lat", "lon", "address"]


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


class PlaceDescriptionContentSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for PlaceDescription model.
    Used in route detail view for minimal description information.
    """

    class Meta:
        model = PlaceDescription
        fields = ["id", "content"]
        read_only_fields = ["id", "content"]


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


class RoutePointDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for RoutePoint used in route detail view.
    Maps 'position' field to 'order' in the output.
    Includes nested Place and Description with minimal fields.
    """

    order = serializers.IntegerField(source="position", read_only=True)
    place = PlaceSimpleSerializer(read_only=True)
    description = PlaceDescriptionContentSerializer(
        read_only=True, allow_null=True
    )  # related_name='description' on model

    class Meta:
        model = RoutePoint
        fields = ["id", "order", "place", "description"]
        read_only_fields = ["id", "order", "place", "description"]


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
    wikipedia_id = serializers.CharField(
        max_length=255, 
        required=False, 
        allow_blank=True,
        help_text="Wikipedia identifier for the place (e.g., 'pl:Pałac Kultury i Nauki')"
    )


class RoutePointCreateSerializer(serializers.ModelSerializer):
    """
    Command Model for adding a point to a manual route.
    Handles nested Place creation/lookup with validation for route type and point limits.
    """

    place = PlaceInputSerializer(write_only=True)

    class Meta:
        model = RoutePoint
        fields = ["place"]

    def validate(self, attrs):
        """
        Validate that the route can accept new points.
        
        Checks:
        - Route must be of type 'manual'
        - Route must not exceed maximum point limit (10 for manual routes)
        
        Args:
            attrs: Dictionary containing validated field data
            
        Returns:
            Validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Get route from context (should be set by the view)
        route = self.context.get('route')
        
        if not route:
            raise serializers.ValidationError(
                "Route context is required.",
                code="route_context_missing"
            )
        
        # Validate route type - only manual routes can have points added
        if route.route_type != Route.TYPE_MANUAL:
            raise serializers.ValidationError(
                "Cannot add points to AI generated route.",
                code="route_type_invalid"
            )
        
        # Validate point limit (max 10 points per manual route)
        current_points_count = RoutePoint.objects.filter(
            route=route, 
            is_removed=False
        ).count()
        
        if current_points_count >= 10:
            raise serializers.ValidationError(
                "Max points limit reached.",
                code="max_points_exceeded"
            )
        
        return attrs

    def create(self, validated_data):
        """
        Create a new RoutePoint with Place lookup/creation logic.
        
        Attempts to find existing Place by osm_id or wikipedia_id.
        If not found, creates a new Place record.
        Automatically calculates the next position in the route.
        
        Args:
            validated_data: Dictionary with validated data including place info
            
        Returns:
            Created RoutePoint instance
            
        Raises:
            serializers.ValidationError: If route context is missing
        """
        place_data = validated_data.pop("place")

        # Lookup logic: Try to find existing place by osm_id or wikipedia_id
        place = None
        osm_id = place_data.get("osm_id")
        wikipedia_id = place_data.get("wikipedia_id")

        # First try osm_id (most reliable identifier)
        if osm_id:
            place = Place.objects.filter(osm_id=osm_id).first()

        # If not found by osm_id, try wikipedia_id
        if not place and wikipedia_id:
            place = Place.objects.filter(wikipedia_id=wikipedia_id).first()

        # If still not found, create new place
        if not place:
            place = Place.objects.create(**place_data)

        # Get route from context (set by view)
        route = self.context.get('route')
        if not route:
            raise serializers.ValidationError("Route context required.")

        # Calculate next position (0-indexed)
        last_position = (
            RoutePoint.objects.filter(route=route, is_removed=False)
            .order_by("-position")
            .values_list("position", flat=True)
            .first()
        )
        position = (last_position if last_position is not None else -1) + 1

        # Create route point with manual source
        route_point = RoutePoint.objects.create(
            route=route, 
            place=place, 
            position=position, 
            source=RoutePoint.SOURCE_MANUAL
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
    Full Route DTO including nested points with detailed information.
    Used for GET /api/routes/{id}/ endpoint.
    
    The 'points' field uses RoutePointDetailSerializer which maps position -> order
    and includes minimal Place and PlaceDescription data.
    The 'user_rating_value' field is annotated in the view's queryset.
    """

    points = RoutePointDetailSerializer(
        many=True, read_only=True
    )  # related_name='points'
    user_rating_value = serializers.IntegerField(
        read_only=True, allow_null=True
    )  # Annotated in queryset

    class Meta:
        model = Route
        fields = ["id", "name", "status", "route_type", "user_rating_value", "points"]
        read_only_fields = [
            "id",
            "name",
            "status",
            "route_type",
            "user_rating_value",
            "points",
        ]


class RouteCreateSerializer(serializers.Serializer):
    """
    Command Model for creating a Route.
    Handles 'ai_generated' vs 'manual' validation logic and Tag association.
    
    Supports two route creation modes:
    1. AI Generated: Requires tags (1-3), optional description (max 1000 chars)
    2. Manual: Optional name, creates empty route for manual point addition
    """

    route_type = serializers.ChoiceField(
        choices=Route.TYPE_CHOICES,
        required=True,
        error_messages={
            "required": "Typ trasy jest wymagany.",
            "invalid_choice": "Nieprawidłowy typ trasy. Dozwolone wartości: 'ai_generated', 'manual'."
        }
    )
    
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.filter(is_active=True),
        many=True,
        required=False,
        error_messages={
            "does_not_exist": "Tag o ID {pk_value} nie istnieje lub jest nieaktywny.",
            "incorrect_type": "Nieprawidłowy typ danych dla tagów. Oczekiwano listy ID."
        }
    )
    
    description = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=1000,
        error_messages={
            "max_length": "Opis nie może przekraczać 1000 znaków."
        }
    )
    
    name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        error_messages={
            "max_length": "Nazwa trasy nie może przekraczać 500 znaków."
        }
    )

    def validate(self, data):
        """
        Cross-field validation for route creation.
        
        Validates that:
        - AI generated routes have 1-3 tags
        - Manual routes don't have tags or description (optional: could allow)
        - Description is only provided for AI generated routes
        
        Args:
            data: Dictionary with validated field data
            
        Returns:
            Validated data dictionary
            
        Raises:
            serializers.ValidationError: If validation rules are violated
        """
        route_type = data.get("route_type")
        tags = data.get("tags", [])
        description = data.get("description", "")
        name = data.get("name", "")

        if route_type == Route.TYPE_AI_GENERATED:
            # AI generated routes require tags
            if not tags:
                raise serializers.ValidationError(
                    {"tags": "Tagi są wymagane dla tras generowanych przez AI."},
                    code="tags_required"
                )
            
            # Validate tag count (1-3)
            if len(tags) < 1:
                raise serializers.ValidationError(
                    {"tags": "Wymagany jest co najmniej 1 tag."},
                    code="tags_min"
                )
            
            if len(tags) > 3:
                raise serializers.ValidationError(
                    {"tags": "Maksymalnie 3 tagi są dozwolone."},
                    code="tags_max"
                )
            
            # Description is optional but validated if provided
            if description and len(description.strip()) > 1000:
                raise serializers.ValidationError(
                    {"description": "Opis nie może przekraczać 1000 znaków."},
                    code="description_too_long"
                )
        
        elif route_type == Route.TYPE_MANUAL:
            # Manual routes should not have tags (business rule for clarity)
            if tags:
                raise serializers.ValidationError(
                    {"tags": "Tagi nie są dozwolone dla tras ręcznych."},
                    code="tags_not_allowed"
                )
            
            # Manual routes should not have description
            if description:
                raise serializers.ValidationError(
                    {"description": "Opis nie jest dozwolony dla tras ręcznych."},
                    code="description_not_allowed"
                )
            
            # Name is optional, will default to "My Custom Trip" if not provided
            if name and not name.strip():
                raise serializers.ValidationError(
                    {"name": "Nazwa trasy nie może być pusta."},
                    code="name_empty"
                )

        return data


class RouteUpdateSerializer(serializers.ModelSerializer):
    """
    Command Model for updating Route status/name.
    Used for PATCH /api/routes/{id}/ endpoint.
    
    Both fields are optional to support partial updates.
    When status changes to 'saved', the saved_at timestamp is automatically set.
    """

    class Meta:
        model = Route
        fields = ["name", "status"]
        extra_kwargs = {
            "name": {"required": False},
            "status": {"required": False},
        }

    def validate_name(self, value: str) -> str:
        """
        Validate route name.
        
        Args:
            value: Route name to validate
            
        Returns:
            Validated name
            
        Raises:
            serializers.ValidationError: If name is empty or too long
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Nazwa trasy nie może być pusta.",
                code="name_empty"
            )
        
        if len(value) > 500:
            raise serializers.ValidationError(
                "Nazwa trasy nie może przekraczać 500 znaków.",
                code="name_too_long"
            )
        
        return value.strip()

    def validate_status(self, value: str) -> str:
        """
        Validate route status.
        
        Args:
            value: Status to validate
            
        Returns:
            Validated status
            
        Raises:
            serializers.ValidationError: If status is invalid
        """
        if value not in [Route.STATUS_TEMPORARY, Route.STATUS_SAVED]:
            raise serializers.ValidationError(
                f"Nieprawidłowy status. Dozwolone wartości: '{Route.STATUS_TEMPORARY}', '{Route.STATUS_SAVED}'.",
                code="status_invalid"
            )
        return value


class RouteOptimizeInputSerializer(serializers.Serializer):
    """
    Input serializer for route optimization endpoint.
    
    Validates optional configuration parameters for the optimization algorithm.
    """

    STRATEGY_NEAREST_NEIGHBOR = 'nearest_neighbor'
    STRATEGY_TSP_APPROX = 'tsp_approx'
    
    STRATEGY_CHOICES = [
        (STRATEGY_NEAREST_NEIGHBOR, 'Nearest Neighbor'),
        (STRATEGY_TSP_APPROX, 'TSP Approximation'),
    ]

    strategy = serializers.ChoiceField(
        choices=STRATEGY_CHOICES,
        default=STRATEGY_NEAREST_NEIGHBOR,
        required=False,
        help_text="Optimization strategy to use"
    )

    def validate_strategy(self, value: str) -> str:
        """
        Validate the optimization strategy.

        Args:
            value: Strategy name to validate

        Returns:
            Validated strategy name

        Raises:
            serializers.ValidationError: If strategy is not supported
        """
        valid_strategies = [choice[0] for choice in self.STRATEGY_CHOICES]
        if value not in valid_strategies:
            raise serializers.ValidationError(
                f"Nieprawidłowa strategia. Dostępne: {', '.join(valid_strategies)}"
            )
        return value


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
