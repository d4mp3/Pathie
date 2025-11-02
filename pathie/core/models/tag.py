"""Tag and RouteTag models definition."""
from django.db import models

from .route import Route


class Tag(models.Model):
    """
    Taxonomy tag for categorizing routes.
    """
    
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tags'
        ordering = ['-priority', 'name']
    
    def __str__(self) -> str:
        return self.name


class RouteTag(models.Model):
    """
    Many-to-many relationship between routes and tags.
    Each route must have 1-3 tags (enforced by SQL trigger).
    """
    
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='route_tags',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.RESTRICT,
        related_name='route_tags',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'route_tags'
        unique_together = [['route', 'tag']]
        indexes = [
            models.Index(
                fields=['tag'],
                name='route_tags_idx_tag',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.route.name} - {self.tag.name}"

