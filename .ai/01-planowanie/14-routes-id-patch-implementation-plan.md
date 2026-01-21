# API Endpoint Implementation Plan: PATCH /api/routes/{id}/

## 1. Przegląd punktu końcowego
Ten plan opisuje wdrożenie metody `PATCH` dla zasobu `routes`, służącej do aktualizacji szczegółów trasy. Głównym celem jest umożliwienie zmiany statusu trasy z "temporary" (tymczasowa) na "saved" (zapisana) oraz aktualizacji jej nazwy. Jest to kluczowy element procesu zapisywania tras wygenerowanych przez AI.

## 2. Szczegóły żądania
- **Metoda HTTP**: `PATCH`
- **Struktura URL**: `/api/routes/{id}/`
- **Parametry**:
  - **Wymagane (Path)**:
    - `id` (integer): Unikalny identyfikator trasy.
  - **Opcjonalne (Body)**:
    - `name` (string): Nowa nazwa trasy.
    - `status` (string): Nowy status trasy (oczekiwana wartość: `"saved"`).

- **Request Body** (Przykład JSON):
  ```json
  {
    "status": "saved",
    "name": "Moja Wycieczka do Paryża"
  }
  ```

## 3. Wymagane komponenty
- **Widok (View)**: `RouteViewSet` (metoda `partial_update`).
- **Serializer**:
  - `RouteUpdateSerializer` (do walidacji danych wejściowych).
  - `RouteDetailSerializer` (do zwrócenia zaktualizowanego obiektu).
- **Serwis (Service)**: `RouteService` (logika biznesowa aktualizacji).
- **Uprawnienia (Permissions)**: `IsAuthenticated`, `IsRouteOwner`.

## 4. Szczegóły odpowiedzi
- **Status 200 OK**: Pomyślna aktualizacja. Zwraca zaktualizowany obiekt trasy.
- **Status 400 Bad Request**: Błędy walidacji (np. za długa nazwa, nieprawidłowy status).
- **Status 404 Not Found**: Trasa nie istnieje lub użytkownik nie ma do niej dostępu.

**Przykład odpowiedzi (200 OK)**:
```json
{
  "id": 123,
  "user_id": 45,
  "name": "Moja Wycieczka do Paryża",
  "status": "saved",
  "route_type": "ai_generated",
  "saved_at": "2026-05-20T14:30:00Z",
  "created_at": "2026-05-20T14:00:00Z",
  "updated_at": "2026-05-20T14:30:00Z"
}
```

## 5. Przepływ danych
1.  **Request**: Żądanie `PATCH /api/routes/{id}/` trafia do `RouteViewSet`.
2.  **Permissions**: Sprawdzenie `IsAuthenticated` oraz `IsOwner` (czy `request.user` jest właścicielem trasy).
3.  **Serializer**: `RouteUpdateSerializer` waliduje dane wejściowe (długość nazwy, poprawność statusu).
4.  **Service**: `RouteViewSet` wywołuje metodę `RouteService.update_route(route, validated_data)`.
    - Serwis aktualizuje pola.
    - Jeśli `status` zmienia się na `saved`, serwis ustawia `saved_at = now()`.
5.  **Database**: Zapis zmian w tabeli `routes` (update timestamp).
6.  **Response**: Zwrócenie zserializowanych danych w formacie `RouteDetailSerializer`.

## 6. Względy bezpieczeństwa
-   **Uwierzytelnianie**: Wymagane (`IsAuthenticated`).
-   **Autoryzacja**: Użytkownik może edytować tylko własne trasy (`IsRouteOwner`).
-   **Walidacja danych**:
    -   Sprawdzenie czy `status` przyjmuje dozwolone wartości (w kontekście API głównie `saved`).
    -   Sanityzacja nazwy trasy (zapobieganie XSS, limity długości).

## 7. Obsługa błędów
-   **ValidationError (400)**: Gdy podano nieprawidłowe dane (np. pusty string jako nazwa).
-   **PermissionDenied (403)**: Gdy użytkownik próbuje edytować cudzą trasę (chociaż standardowo DRF dla `get_object` zwraca 404 w przypadku braku dostępu przy querysecie filtrowanym po użytkowniku).
-   **NotFound (404)**: Gdy ID trasy nie istnieje.

## 8. Rozważania dotyczące wydajności
-   Operacja jest prosta (aktualizacja jednego wiersza po ID), nie generuje problemu N+1.
-   Jeśli w przyszłości aktualizacja będzie wpływać na powiązane tagi lub punkty, należy zadbać o transakcyjność (`transaction.atomic`).

## 9. Etapy wdrożenia

### Krok 1: Utworzenie Serializera Aktualizacji
W pliku `routes/serializers.py`:
-   Stwórz `RouteUpdateSerializer` dziedziczący po `serializers.ModelSerializer`.
-   Pola: `name`, `status`.
-   Ustaw oba pola jako `required=False` (dla PATCH).
-   Dodaj walidację dla `status`, aby akceptował `saved` (i ewentualnie `temporary`, choć przejście w drugą stronę może nie byc obsługiwane).

### Krok 2: Implementacja Logiki w Serwisie
W pliku `routes/services.py`:
-   Dodaj metodę `update_route(self, route: Route, data: dict) -> Route`.
-   Zaimplementuj logikę:
    -   Aktualizacja pól z `data`.
    -   Jeśli `data.get('status') == 'saved'` i `route.status != 'saved'`, ustaw `route.saved_at = timezone.now()`.
    -   Zapisz obiekt (`route.save()`).

### Krok 3: Aktualizacja ViewSetu
W pliku `routes/views.py`:
-   W `RouteViewSet`:
    -   Upewnij się, że `serializer_class` wskazuje na `RouteUpdateSerializer` dla akcji `partial_update` (można nadpisać `get_serializer_class`).
    -   W metodzie `perform_update` (lub nadpisując `partial_update`) wywołaj `RouteService.update_route`.

### Krok 4: Testy
-   Test jednostkowy zmiany nazwy.
-   Test jednostkowy zmiany statusu na `saved` (weryfikacja ustawienia `saved_at`).
-   Test próby edycji cudzej trasy (404/403).
-   Test walidacji niepoprawnych danych.
