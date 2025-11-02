"""Route model definition."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Route(models.Model):
    """
    User's travel route - can be AI-generated or manually created.
    """
    
    STATUS_TEMPORARY = 'temporary'
    STATUS_SAVED = 'saved'
    STATUS_CHOICES = [
        (STATUS_TEMPORARY, 'Temporary'),
        (STATUS_SAVED, 'Saved'),
    ]
    
    TYPE_AI_GENERATED = 'ai_generated'
    TYPE_MANUAL = 'manual'
    TYPE_CHOICES = [
        (TYPE_AI_GENERATED, 'AI Generated'),
        (TYPE_MANUAL, 'Manual'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routes',
        db_index=True,
    )
    name = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True,
    )
    route_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )
    saved_at = models.DateTimeField(null=True, blank=True)
    cached_at = models.DateTimeField(null=True, blank=True)
    cache_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'routes'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['user', 'status', '-created_at'],
                name='routes_idx_usr_stat_cr',
            ),
            models.Index(
                fields=['route_type'],
                name='routes_idx_type',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.get_status_display()})"
    
    def clean(self) -> None:
        """Validate model constraints."""
        super().clean()
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError({'status': f'Invalid status: {self.status}'})
        if self.route_type not in dict(self.TYPE_CHOICES):
            raise ValidationError({'route_type': f'Invalid route type: {self.route_type}'})

