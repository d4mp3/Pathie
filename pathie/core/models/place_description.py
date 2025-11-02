"""PlaceDescription model definition."""
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models

from .route_point import RoutePoint


class PlaceDescription(models.Model):
    """
    AI-generated description for a place in a specific route context.
    """
    
    route_point = models.OneToOneField(
        RoutePoint,
        on_delete=models.CASCADE,
        related_name='description',
    )
    language_code = models.CharField(
        max_length=8,
        default='pl',
    )
    content = models.TextField(
        validators=[
            MinLengthValidator(2500),
            MaxLengthValidator(5000),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'place_descriptions'
        ordering = ['route_point']
    
    def __str__(self) -> str:
        return f"Description for {self.route_point.place.name} [{self.language_code}]"
    
    def clean(self) -> None:
        """Validate model constraints."""
        super().clean()
        content_length = len(self.content)
        if not (2500 <= content_length <= 5000):
            raise ValidationError({
                'content': f'Content must be between 2500 and 5000 characters (current: {content_length})'
            })

