"""Place model definition."""
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Place(models.Model):
    """
    Geographic place/point of interest (from OSM, Wikipedia, etc.).
    """
    
    name = models.TextField()
    osm_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    wikipedia_id = models.TextField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    address = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    country = models.TextField(null=True, blank=True)
    lat = models.FloatField(
        validators=[
            MinValueValidator(-90.0),
            MaxValueValidator(90.0),
        ],
    )
    lon = models.FloatField(
        validators=[
            MinValueValidator(-180.0),
            MaxValueValidator(180.0),
        ],
    )
    data = models.JSONField(
        null=True,
        blank=True,
        help_text='Additional data from OSM/Wikipedia',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'places'
        ordering = ['name']
        indexes = [
            models.Index(
                fields=['lat', 'lon'],
                name='places_idx_lat_lon',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.lat}, {self.lon})"
    
    def clean(self) -> None:
        """Validate model constraints."""
        super().clean()
        if not (-90 <= self.lat <= 90):
            raise ValidationError({'lat': 'Latitude must be between -90 and 90'})
        if not (-180 <= self.lon <= 180):
            raise ValidationError({'lon': 'Longitude must be between -180 and 180'})

