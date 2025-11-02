"""Rating model definition."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .place_description import PlaceDescription
from .route import Route


class Rating(models.Model):
    """
    User rating for routes or place descriptions.
    Each user can rate each target once.
    """
    
    TYPE_PLACE_DESCRIPTION = 'place_description'
    TYPE_ROUTE = 'route'
    TYPE_CHOICES = [
        (TYPE_PLACE_DESCRIPTION, 'Place Description'),
        (TYPE_ROUTE, 'Route'),
    ]
    
    VALUE_DOWNVOTE = -1
    VALUE_UPVOTE = 1
    VALUE_CHOICES = [
        (VALUE_DOWNVOTE, 'Downvote'),
        (VALUE_UPVOTE, 'Upvote'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    rating_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )
    rating_value = models.SmallIntegerField(
        choices=VALUE_CHOICES,
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True,
    )
    place_description = models.ForeignKey(
        PlaceDescription,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ratings'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['user'],
                name='ratings_idx_user',
            ),
        ]
    
    def __str__(self) -> str:
        target = self.route or self.place_description
        vote = 'upvote' if self.rating_value == self.VALUE_UPVOTE else 'downvote'
        return f"{self.user.username} {vote} on {target}"
    
    def clean(self) -> None:
        """Validate model constraints."""
        super().clean()
        
        # Validate rating_value
        if self.rating_value not in [self.VALUE_DOWNVOTE, self.VALUE_UPVOTE]:
            raise ValidationError({
                'rating_value': f'Rating value must be -1 or 1, got {self.rating_value}'
            })
        
        # Validate rating_type matches target
        if self.rating_type == self.TYPE_ROUTE:
            if not self.route or self.place_description:
                raise ValidationError(
                    "For rating_type='route', route must be set and place_description must be null"
                )
        elif self.rating_type == self.TYPE_PLACE_DESCRIPTION:
            if not self.place_description or self.route:
                raise ValidationError(
                    "For rating_type='place_description', place_description must be set and route must be null"
                )
        else:
            raise ValidationError({'rating_type': f'Invalid rating_type: {self.rating_type}'})

