# API Endpoint Implementation Plan: Szczegóły Trasy

## 1. Przegląd punktu końcowego
Celem tego punktu końcowego jest pobranie pełnych szczegółów konkretnej trasy (Route) należącej do użytkownika. Zwracane dane obejmują podstawowe informacje o trasie, uporządkowaną listę punktów trasy (Route Points) wraz ze szczegółami miejsc (Places) i wygenerowanymi opisami (Place Descriptions). Punkt końcowy uwzględnia również ewentualną ocenę wystawioną trasie przez użytkownika. Jest to kluczowy widok dla aplikacji klienckiej do wyświetlania mapy i planu wycieczki.

## 2. Szczegóły żądania
- **Metoda HTTP**: `GET`
- **Struktura URL**: `/api/routes/{id}/`
- **Parametry**:
  - **Wymagane**:
    - `id` (path parameter, integer): Unikalny identyfikator trasy.
  - **Opcjonalne**: Brak.
- **Request Body**: Brak.

## 3. Szczegóły odpowiedzi
- **Kod sukcesu**: `200 OK`
- **Struktura JSON**:
  ```json
  {
    "id": 101,
    "name": "Warsaw Old Town",
    "status": "temporary", // 'temporary' lub 'saved'
    "route_type": "ai_generated", // 'ai_generated' lub 'manual'
    "user_rating_value": 1, // 1 (like), -1 (dislike) lub null
    "points": [
      {
        "id": 501,
        "order": 1, // Odpowiada polu 'position'
        "place": {
          "id": 200,
          "name": "Royal Castle",
          "lat": 52.248,
          "lon": 21.015,
          "address": "Plac Zamkowy 4"
        },
        "description": {
          "id": 901,
          "content": "A detailed AI-generated story..."
        }
      }
    ]
  }
  ```
- **Kody błędów**:
  - `404 Not Found`: Gdy trasa nie istnieje lub nie należy do zalogowanego użytkownika.
  - `401 Unauthorized`: Gdy użytkownik nie jest zalogowany.

## 4. Wymagane komponenty

### Modele
- `Route` (`pathie.core.models`): Model główny.
- `RoutePoint`: Do pobrania punktów.
- `Place`: Do szczegółów miejsca.
- `PlaceDescription`: Do opisów punktów.
- `Rating`: Do pobrania oceny użytkownika (`user_rating_value`).

### Serializery
Wymagane utworzenie nowych lub rozszerzenie istniejących serializerów w `pathie.api.serializers`:

1.  **`PlaceSimpleSerializer`**:
    -   Pola: `id`, `name`, `lat`, `lon`, `address`.
2.  **`PlaceDescriptionContentSerializer`**:
    -   Pola: `id`, `content`.
3.  **`RoutePointDetailSerializer`**:
    -   Pola: `id`, `order` (mapowane z `position`), `place` (Nested `PlaceSimpleSerializer`), `description` (Nested `PlaceDescriptionContentSerializer`, allow_null=True).
4.  **`RouteDetailSerializer`**:
    -   Pola: `id`, `name`, `status`, `route_type`, `user_rating_value`, `points`.
    -   Pole `user_rating_value`: `serializers.IntegerField(allow_null=True)`.
    -   Pole `points`: `RoutePointDetailSerializer(many=True, source='route_points')`.

### Widoki
- **`RouteDetailView`** (rozszerzający `RetrieveAPIView`):
    -   Queryset podstawowy: `Route.objects.all()`.
    -   Permission classes: `[IsAuthenticated]`.

## 5. Przepływ danych
1.  **Żądanie**: Klient wysyła `GET /api/routes/101/`.
2.  **Autoryzacja**: DRF sprawdza token JWT (`IsAuthenticated`).
3.  **Widok (`get_queryset`)**:
    -   Filtruje trasy do tych należących do `request.user`.
    -   Optymalizuje zapytanie używając `prefetch_related` dla `route_points`, `route_points__place`, `route_points__place_description`.
    -   (Opcjonalnie) Używa podzapytania (Subquery) lub osobnego zapytania w SerializerMethodField do pobrania `user_rating_value` z tabeli `ratings` gdzie `rating_type='route'`. Z uwagi na relację 1:N w `ratings`, należy wyszukać ocenę konkretnego użytkownika dla tej trasy.
4.  **Pobranie Obiektu**: `get_object()` instancjonuje obiekt lub rzuca `Http404`.
5.  **Serializacja**: `RouteDetailSerializer` przetwarza obiekt trasy na JSON.
    -   Lista `points` jest sortowana rosnąco według pola `position`.
6.  **Odpowiedź**: Zwrócenie JSON z kodem 200.

## 6. Względy bezpieczeństwa
-   **Izolacja danych użytkownika**: Użytkownik **musi** mieć dostęp tylko do własnych tras. Należy to wyegzekwować poprzez filtrowanie w `get_queryset` (`.filter(user=self.request.user)`).
-   **Identyfikacja zasobów**: Użycie standardowego mechanizmu `lookup_field='id'`. Próba dostępu do ID innej osoby (nawet istniejącego w bazie) musi skutkować błędem 404 (nie 403), aby nie ujawniać istnienia zasobu.

## 7. Obsługa błędów
-   **Nieznalezienie zasobu**: Wyjątek `Http404` z DRF zostanie automatycznie przekształcony w odpowiedź JSON z kodem 404.
-   **Błędy bazy danych**: Standardowa obsługa wyjątków Django/DRF (kod 500 w przypadku awarii połączenia).

## 8. Wydajność
-   **Problem N+1**: Głównym zagrożeniem jest pobieranie każdego punktu, miejsca i opisu w oddzielnych zapytaniach.
    -   **Rozwiązanie**: Należy bezwzględnie użyć `prefetch_related` w `get_queryset`:
        ```python
        queryset = Route.objects.filter(user=user).prefetch_related(
            'route_points',
            'route_points__place',
            'route_points__place_description'
        )
        ```
-   **Sortowanie**: Punkty powinny być posortowane na poziomie bazy danych lub `Prefetch` object (`queryset=RoutePoint.objects.order_by('position')`).

## 9. Etapy wdrożenia

1.  **Definicja Serializerów** (`pathie/api/routes/serializers.py`):
    -   Zaimplementuj `PlaceSimpleSerializer`.
    -   Zaimplementuj `PlaceDescriptionContentSerializer`.
    -   Zaimplementuj `RoutePointDetailSerializer` z mapowaniem `position` -> `order`.
    -   Zaimplementuj `RouteDetailSerializer` z obsługą `user_rating_value`.

2.  **Implementacja Widoku** (`pathie/api/routes/views.py`):
    -   Utwórz klasę `RouteDetailView`.
    -   Zdefiniuj `get_queryset` z odpowiednim filtrowaniem (per user) i optymalizacją (prefetch).
    -   Dodaj logikę wyciągania oceny użytkownika (można użyć adnotacji `Route.objects.annotate(user_rating_value=Subquery(...))` dla wydajności lub prostej metody w serializerze). Zalecana adnotacja dla czystości.

3.  **Konfiguracja URL** (`pathie/api/routes/urls.py`):
    -   Dodaj ścieżkę `<int:pk>/` (lub `<int:id>/` zależnie od konwencji) wskazującą na `RouteDetailView`.

4.  **Testy Manualne**:
    -   Sprawdź poprawną strukturę JSON.
    -   Sprawdź sortowanie punktów.
    -   Sprawdź dostęp do cudzej trasy (powinien być 404).

5.  **Weryfikacja**:
    -   Uruchomienie endpointa i sprawdzenie liczby zapytań SQL w debug toolbarze (powinna być stała niezależnie od liczby punktów).
