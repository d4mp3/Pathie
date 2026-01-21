# API Endpoint Implementation Plan: Lista Tras Użytkownika (GET /api/routes/)

## 1. Przegląd punktu końcowego
Celem tego endpointu jest umożliwienie zalogowanemu użytkownikowi pobrania listy swoich tras (Route). Endpoint obsługuje filtrowanie po statusie (np. `saved`, `temporary`), sortowanie oraz paginację. Zwraca podstawowe informacje o trasie wraz z liczbą punktów (`points_count`), co pozwala na wyświetlenie listy tras w interfejsie użytkownika.

## 2. Szczegóły żądania
- **Metoda HTTP**: `GET`
- **Struktura URL**: `/api/routes/`
- **Uwierzytelnianie**: Wymagany nagłówek `Authorization: Bearer <token>` (Tylko zalogowani użytkownicy)
- **Parametry zapytania (Query Parameters)**:
  - **Wymagane**: Brak (domyślne wartości są stosowane).
  - **Opcjonalne**:
    - `page`: `int` — numer strony wyników (domyślnie 1).
    - `status`: `str` — status trasy do filtrowania (`temporary`, `saved`). Domyślnie: `saved`.
    - `ordering`: `str` — pole do sortowania (np. `-created_at`, `name`). Obsługiwane prefiksy `-` dla sortowania malejącego.
- **Request Body**: Brak.

## 3. Szczegóły odpowiedzi
- **Kod statusu**: `200 OK`
- **Typ zawartości**: `application/json`
- **Struktura Payloadu**:
  ```json
  {
    "count": 15,
    "next": "https://api.example.com/api/routes/?page=2",
    "previous": null,
    "results": [
      {
        "id": 101,
        "name": "Warsaw Old Town",
        "status": "saved",
        "route_type": "ai_generated",
        "created_at": "2024-01-01T12:00:00Z",
        "points_count": 5
      }
    ]
  }
  ```

## 4. Wymagane komponenty (Modele, Serializery, Widoki)

### Modele (istniejące)
- **`routes.models.Route`**: Główny model trasy. Wymaga weryfikacji indeksów dla pól `user_id` oraz `status`.
- **`routes.models.RoutePoint`**: Powiązany model punktów (relacja FK `route_id`), wykorzystywany do obliczenia `points_count`.

### Serializery
- **`RouteListSerializer`** (w `routes/api/serializers.py`):
  - Pola: `id`, `name`, `status`, `route_type`, `created_at`, `points_count`.
  - Pola tylko do odczytu: Wszystkie.
  - Pole `points_count`: `serializers.IntegerField()`. Wartość będzie dostarczana przez adnotację w querysecie.

### Warstwa Serwisowa / Selektory (Business Logic)
- **`routes.services.selectors.route_list_selector`** (lub `get_user_routes`):
  - Funkcja odpowiedzialna za pobranie querysetu dla danego użytkownika (`Route.objects.filter(user=user)`).
  - Aplikacja filtrów (`status`) i sortowania.
  - Optymalizacja zapytania poprzez `annotate` dla `points_count` (liczenie powiązanych `route_points`, z uwzględnieniem `is_removed=False`).

### Widoki
- **`RouteListApi`** (lub `RouteViewSet` z akcją `list`) w `routes/api/views.py`:
  - Dziedziczy po `generics.ListAPIView`.
  - Permission: `IsAuthenticated`.
  - Pagination Class: Standardowa paginacja projektu (np. `StandardResultsSetPagination`).
  - Filter Backends: Własna obsługa w selektorze lub `DjangoFilterBackend` + `OrderingFilter`.

## 5. Przepływ danych
1.  **Żądanie**: Klient wysyła `GET /api/routes/?status=saved`.
2.  **Widok (`RouteListApi`)**:
    -   Weryfikuje token użytkownika (`request.user`).
    -   Wywołuje selektor `route_list_selector(user=request.user, filters=request.query_params)`.
3.  **Selektor (`Business Logic`)**:
    -   Buduje zapytanie ORM: `Route.objects.filter(user=request.user)`.
    -   Aplikuje filtr `status='saved'`.
    -   Wykonuje adnotację: `.annotate(points_count=Count('route_points', filter=Q(route_points__is_removed=False)))`.
    -   Aplikuje sortowanie (domyślnie `-created_at`).
4.  **Serializer (`RouteListSerializer`)**:
    -   Przekształca obiekty `Route` (wraz z `points_count`) na JSON.
5.  **Odpowiedź**: Zwraca paginowaną listę w formacie JSON.

## 6. Względy bezpieczeństwa
-   **Uwierzytelnianie**: Bezwzględnie wymagane (`IsAuthenticated`). Anonimowi użytkownicy otrzymują `401 Unauthorized`.
-   **Izolacja danych (Multi-tenancy)**: Zapytanie musi zawsze filtrować po `user_id` bieżącego użytkownika (`request.user`), aby użytkownik nie widział tras innych osób.
-   **Walidacja wejścia**:
    -   Parametr `status` powinien być sprawdzany względem dozwolonych wartości (`saved`, `temporary`). Błędna wartość może być ignorowana (fallback do domyślnej) lub zwracać `400 Bad Request` (zależnie od konwencji projektu, sugerowane `400` przy błędnym typie).

## 7. Obsługa błędów
-   **401 Unauthorized**: Brak lub nieprawidłowy token.
-   **400 Bad Request**: Nieprawidłowe parametry zapytania (np. nieistniejące pole w `ordering`).
-   **500 Internal Server Error**: Nieoczekiwany błąd serwera/bazy danych.

## 8. Rozważania dotyczące wydajności
-   **N+1 Queries**: Użycie `annotate()` dla `points_count` (SQL `COUNT` z `GROUP BY`) zapobiega problemowi N+1 (pobierania punktów dla każdej trasy osobno).
-   **Indeksy**:
    -   Upewnić się, że istnieje indeks na kolumnie `user_id` (Postgres tworzy go automatycznie dla FK).
    -   Rozważyć indeks złożony `(user_id, status, created_at)` jeśli tabela `routes` będzie bardzo duża, aby przyspieszyć filtrowanie i sortowanie dla konkretnego użytkownika.
-   **Paginacja**: Ogranicza ilość przesyłanych i przetwarzanych danych jednorazowo.

## 9. Etapy wdrożenia
1.  **Analiza Modelu**: Sprawdzenie modelu `Route` i `RoutePoint` pod kątem wymaganych pól i relacji.
2.  **Stworzenie Serializera**: Implementacja `RouteListSerializer` w `routes/api/serializers.py` z polem `points_count` (IntegerField).
3.  **Implementacja Logiki (Selector)**: Stworzenie funkcji w `routes/services/selectors.py` zwracającej opisany queryset.
4.  **Stworzenie Widoku**: Implementacja `RouteListApi` w `routes/api/views.py` wykorzystującego stworzony selektor i serializer.
5.  **Konfiguracja URL**: Dodanie wpisu w `routes/urls.py` (lub głównym `api/urls.py`) mapującego `/api/routes/` na widok.
6.  **Testy**:
    -   Unit testy serializera.
    -   Testy integracyjne API (sprawdzenie statusów HTTP 200, 401, poprawności filtrowania po statusie i izolacji danych użytkownika).
