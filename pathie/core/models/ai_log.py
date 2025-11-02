"""AIGenerationLog model definition."""
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .route import Route


class AIGenerationLog(models.Model):
    """
    Log of AI generation requests for routes.
    Tracks model usage, tokens, costs, and generation parameters.
    """
    
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='ai_logs',
    )
    model = models.TextField()
    provider = models.TextField(null=True, blank=True)
    prompt_hash = models.TextField(null=True, blank=True)
    tags_snapshot = ArrayField(
        models.TextField(),
        default=list,
        blank=True,
        help_text='Tags at time of generation',
    )
    additional_text_snapshot = models.TextField(null=True, blank=True)
    points_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(7),
        ],
    )
    tokens_prompt = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    tokens_completion = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    request_id = models.TextField(null=True, blank=True)
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text='Additional metadata',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_generation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['route', '-created_at'],
                name='ai_log_idx_route_created',
            ),
        ]
    
    def __str__(self) -> str:
        return f"AI log for {self.route.name} using {self.model}"

