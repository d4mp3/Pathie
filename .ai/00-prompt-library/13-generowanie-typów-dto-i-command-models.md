Jesteś wykwalifikowanym programistą Python/Django, specjalizującym się w budowie REST API przy użyciu Django REST Framework (DRF). Twoim zadaniem jest stworzenie warstwy serializacji (DTO i Command Models) dla aplikacji Pathie.

Twoim celem jest przeanalizowanie modeli bazy danych (Django Models) oraz planu API, a następnie utworzenie odpowiednich Serializerów, które będą pełnić rolę DTO (dla odczytu danych) oraz Command Models (dla walidacji danych wejściowych).

Najpierw dokładnie przejrzyj następujące dane wejściowe:

1. Modele bazy danych (Django ORM):
<database_models>
{{db-models}}
</database_models>

2. Plan API (zawierający definicje payloadów i endpointów):
<api_plan>
{{api-plan}}
</api_plan>

Twoim zadaniem jest utworzenie kodu Python zawierającego definicje Serializerów w `serializers.py`. Wykonaj następujące kroki:

1. Przeanalizuj modele bazy danych i plan API pod kątem wymaganych struktur danych.
2. Utwórz Serializery (klasy dziedziczące po `rest_framework.serializers.Serializer` lub `ModelSerializer`).
   - Dla **DTO** (odczyt): Użyj `ModelSerializer` tam gdzie to możliwe, aby zachować zgodność z ORM, lub zwykłych `Serializer` dla niestandardowych struktur.
   - Dla **Command Models** (zapis/akcje): Utwórz serializery walidujące dane wejściowe (Input Serializers). Pamiętaj o regułach walidacji określonych w PRD/API Plan.
3. Zapewnij mapowanie nazw pól i typów zgodnie z kontraktem API (camelCase vs snake_case - jeśli wymagane, lub standardowe dla Python snake_case).
4. Wykonaj końcowe sprawdzenie, czy wszystkie endpointy z planu API mają pokrycie w serializerach.

Przed utworzeniem ostatecznego wyniku, pracuj wewnątrz tagów <analysis> w swoim bloku myślenia:
- Wymień wszystkie potrzebne serializery na podstawie Planu API.
- Dla każdego z nich określ:
  - Czy jest to DTO (odczyt) czy Command (zapis).
  - Z jakim modelem bazy danych jest powiązany (jeśli dotyczy).
  - Jakie pola musi zawierać i jakie reguły walidacji (np. `required`, `min_length`, `validators`) zastosować.
- Rozważ odpowiednie struktury dla zagnieżdżonych danych (Nested Serializers).

Po przeprowadzeniu analizy, podaj ostateczny kod Python, który trafi do pliku (np. `pathie_app/api/serializers.py`).

Pamiętaj:
- Kod musi być zgodny z **Python 3.10+** tzn korzystać z nowoczesnych type hints, ale w kontekście Django DRF.
- Stosuj konwencję nazewniczą: `[Resource]Serializer` dla ogólnych, `[Resource]CreateSerializer` / `[Resource]UpdateSerializer` dla specyficznych akcji (Command Models), lub `[Resource]ReadSerializer` dla DTO, jeśli struktury się różnią.
- Komentarze / Docstringi powinny wyjaśniać niestandardową logikę.
- Uwzględnij wymagania **MVP** i **Stacku** (Django Monolith, DRF) - nie komplikuj przesadnie (np. unikaj nadmiarowych warstw abstrakcji, jeśli `ModelSerializer` wystarczy).

Końcowy wynik powinien składać się wyłącznie z kodu Python (zawartość pliku `serializers.py`).
