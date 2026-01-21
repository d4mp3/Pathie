# API Endpoint Implementation Plan: Remove Route Point

## 1. Przegląd punktu końcowego
Punkt końcowy `DELETE /api/routes/{id}/points/{point_id}/` służy do usuwania konkretnego punktu z trasy użytkownika. Ze względu na strukturę bazy danych (obecność flagi `is_removed` w tabeli `route_points` oraz powiązania z kosztownymi w generowaniu opisami AI), operacja ta zostanie zaimplementowana jako **Soft Delete** (oflagowanie jako usunięte), a nie fizyczne usunięcie rekordu z bazy.

## 2. Szczegóły żądania
- **Metoda HTTP**: `DELETE`
- **Struktura URL**: `/api/routes/{id}/points/{point_id}/`
- **Parametry**:
  - **Wymagane (Path Parameters)**:
    - `id`: Integer - Unikalny identyfikator trasy.
    - `point_id`: Integer - Unikalny identyfikator punktu trasy (`route_point`).
  - **Opcjonalne**: Brak.
- **Request Body**: Brak.

## 3. Wymagane komponenty

### Modele (`models.py`)
- Bez zmian w strukturze. Wykorzystujemy istniejące pole `route_points.is_removed`.

### Widoki (`views.py`)
- **Widok**: Metoda `destroy` w `RoutePointViewSet` (lub dedykowana akcja, jeśli `destroy` domyślnie robi hard delete, ale w DRF można nadpisać `perform_destroy`).
- **Klasa bazowa**: `mixins.DestroyModelMixin`, `GenericViewSet` (lub w ramach `ModelViewSet`).

### Uprawnienia (`permissions.py`)
- `IsAuthenticated`: Użytkownik musi być zalogowany.
- `IsRouteOwner`: Użytkownik musi być właścicielem trasy powiązanej z punktem.

### Serwisy (`services.py`)
- `RouteService.soft_delete_point(route_point: RoutePoint) -> None`:
  - Metoda enkapsulująca logikę biznesową ustawiania flagi `is_removed = True`.
  - Opcjonalnie: Przeliczenie kolejności (jeśli wymagane przez frontend, choć zazwyczaj sortowanie po `position` i filtrowanie `is_removed=False` wystarczy).

## 4. Szczegóły odpowiedzi
- **Sukces**:
  - **Kod**: `204 No Content`
  - **Body**: Puste.
- **Błędy**:
  - `401 Unauthorized`: Brak tokena uwierzytelniającego.
  - `404 Not Found`: Trasa lub punkt nie istnieje, lub punkt nie należy do podanej trasy/użytkownika.

## 5. Przepływ danych
1.  **Request**: Klient wysyła żądanie `DELETE` z `id` i `point_id`.
2.  **View (Permissions)**:
    - Sprawdzenie tokena (`IsAuthenticated`).
    - Pobranie trasy na podstawie `id` i `user=request.user`. Jeśli nie znaleziono -> `404`.
3.  **View (Query)**:
    - Pobranie punktu `route_points` gdzie `id=point_id` ORAZ `route_id=id` (oraz `is_removed=False` jeśli nie chcemy usuwać już usuniętych, choć `204` jest też ok dla idempotencji).
    - Jeśli punkt nie istnieje -> `404`.
4.  **View (Action)**:
    - Wywołanie `perform_destroy(instance)`.
5.  **Service/Logic**:
    - W nadpisanej metodzie `perform_destroy` (lub serwisie) ustawienie `instance.is_removed = True`.
    - Zapisanie zmiany: `instance.save(update_fields=['is_removed'])`.
6.  **Response**: Zwrócenie `204 No Content`.

## 6. Względy bezpieczeństwa
- **Autoryzacja właściciela**: Kluczowe jest upewnienie się, że usuwany punkt należy do trasy, która należy do zalogowanego użytkownika.
- **Spójność danych**: Walidacja, czy `point_id` faktycznie odnosi się do `route_id` podanego w URL. Zapobiega to błędom logicznym, gdzie użytkownik mógłby próbować usunąć punkt z innej trasy, znając jego ID.

## 7. Obsługa błędów
- **Standardowe wyjątki Django/DRF**:
  - `Http404`: Zwracane, gdy obiekt nie zostanie znaleziony (QuerySet filtrowany po użytkowniku).
- **Logowanie**:
  - Logowanie zdarzenia usunięcia punktu (poziom INFO).

## 8. Rozważania dotyczące wydajności
- **Indeksy**: Pola `id` (PK) oraz FK (`route_id`, `user_id`) są indeksowane, więc wyszukiwanie będzie szybkie.
- **Update**: Aktualizacja pojedynczego pola boolowskiego jest bardzo lekka.

## 9. Etapy wdrożenia

1.  **Aktualizacja/Weryfikacja Permissions**:
    - Upewnij się, że istnieje klasa uprawnień sprawdzająca własność trasy (np. `IsRouteOwner`).

2.  **Implementacja Widoku (`views.py`)**:
    - Utwórz lub zaktualizuj `RoutePointViewSet` (lub zagnieżdżony widok).
    - Zaimplementuj metodę `destroy` lub nadpisz `perform_destroy`.
    ```python
    def perform_destroy(self, instance):
        # Soft delete implementation
        instance.is_removed = True
        instance.save(update_fields=['is_removed'])
    ```

3.  **Rejestracja URL (`urls.py`)**:
    - Upewnij się, że endpoint jest poprawnie zmapowany w routerze DRF, np. przy użyciu `drf-nested-routers` dla struktury `/routes/{route_pk}/points/{pk}/` lub płaskiej struktury, jeśli tak zdecydowano (specyfikacja sugeruje zagnieżdżenie).

4.  **Testy (`tests.py`)**:
    - Test: Użytkownik usuwa swój punkt -> 204, w bazie `is_removed=True`.
    - Test: Użytkownik próbuje usunąć cudzy punkt -> 404.
    - Test: Użytkownik próbuje usunąć nieistniejący punkt -> 404.
    - Test: Sprawdzenie, czy `place_description` nadal istnieje po usunięciu punktu (potwierdzenie soft delete).
