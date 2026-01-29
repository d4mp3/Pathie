"""Management command to seed initial tags."""

from django.core.management.base import BaseCommand
from core.models import Tag


class Command(BaseCommand):
    help = "Seeds the database with initial tags based on PRD"

    def handle(self, *args, **options):
        tags_data = [
            {
                "name": "Sztuka",
                "description": "Galerie sztuki, muzea, wystawy, street art i instalacje artystyczne.",
                "priority": 100,
            },
            {
                "name": "Historia",
                "description": "Zabytki, pomniki, miejsca pamięci, muzea historyczne i dawna architektura.",
                "priority": 90,
            },
            {
                "name": "Kuchnia",
                "description": "Lokalne restauracje, kawiarnie, targi żywności i miejsca z tradycyjnymi potrawami.",
                "priority": 80,
            },
            {
                "name": "Architektura",
                "description": "Unikalne budynki, style architektoniczne, mosty i nowoczesne konstrukcje.",
                "priority": 70,
            },
            {
                "name": "Natura",
                "description": "Parki, ogrody botaniczne, tereny zielone i rezerwaty przyrody.",
                "priority": 60,
            },
            {
                "name": "Rozrywka",
                "description": "Teatry, kina, kluby muzyczne, centra rozrywki i życie nocne.",
                "priority": 50,
            },
            {
                "name": "Nauka",
                "description": "Centra nauki, planetaria, obserwatoria i muzea techniki.",
                "priority": 40,
            },
        ]

        created_count = 0
        updated_count = 0

        for tag_data in tags_data:
            tag, created = Tag.objects.update_or_create(
                name=tag_data["name"],
                defaults={
                    "description": tag_data["description"],
                    "priority": tag_data["priority"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded tags: {created_count} created, {updated_count} updated"
            )
        )
