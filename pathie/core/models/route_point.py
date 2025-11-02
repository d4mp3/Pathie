"""RoutePoint model definition."""
from django.core.exceptions import ValidationError
from django.db import models

from .place import Place
from .route import Route


class RoutePoint(models.Model):
    """
    A point (place) on a specific route with ordering information.
    """
    
    SOURCE_AI_GENERATED = 'ai_generated'
    SOURCE_MANUAL = 'manual'
    SOURCE_CHOICES = [
        (SOURCE_AI_GENERATED, 'AI Generated'),
        (SOURCE_MANUAL, 'Manual'),
    ]
    
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='points',
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='route_points',
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
    )
    position = models.IntegerField(
        help_text='Base position in route',
    )
    optimized_position = models.IntegerField(
        null=True,
        blank=True,
        help_text='Position after optimization',
    )
    is_removed = models.BooleanField(
        default=False,
        db_index=True,
    )
    added_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'route_points'
        ordering = ['route', 'position']
        indexes = [
            models.Index(
                fields=['route', 'position'],
                name='rp_idx_route_pos',
            ),
            models.Index(
                fields=['route', 'is_removed'],
                name='rp_idx_route_removed',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.place.name} at position {self.position} in {self.route.name}"
    
    def clean(self) -> None:
        """Validate model constraints."""
        super().clean()
        if self.source not in dict(self.SOURCE_CHOICES):
            raise ValidationError({'source': f'Invalid source: {self.source}'})

