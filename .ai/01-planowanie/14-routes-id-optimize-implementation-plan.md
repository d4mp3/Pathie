<analysis>
1.  **Podsumowanie specyfikacji API**:
    *   **Cel**: Uruchomienie algorytmu optymalizacji kolejności punktów dla trasy.
    *   **Ograniczenia**: Tylko dla tras typu `manual`. Wymaga odpowiedniej liczby punktów.
    *   **Wejście**: `id` trasy w URL. Body puste lub z parametrami konfiguracyjnymi (na razie puste/domyślne).
    *   **Wyjście**: Lista punktów trasy w nowej kolejności.

2.  **Parametry**:
    *   **Wymagane**: `id` (ścieżka URL).
    *   **Opcjonalne**: Konfiguracja algorytmu w body (JSON), np. `strategy` (domyślnie 'TSP' lub 'shortest_path').

3.  **Szczegóły Modelu i Serializerów**:
    *   **Modele**: `Route` (odczyt, walidacja typu), `RoutePoint` (odczyt, aktualizacja `position` lub `optimized_position`).
    *   **Serializery**:
        *   `RouteOptimizeSerializer` (wejściowy): Walidacja opcjonalnych parametrów konfiguracyjnych.
        *   `RoutePointSerializer` (wyjściowy): Serializacja listy punktów (taka sama struktura jak w szczegółach trasy).

4.  **Logika Biznesowa (Services)**:
    *   Miejsce: `RouteService` w `services.py`.
    *   Metoda: `optimize_route(route: Route, config: dict) -> List[RoutePoint]`.
    *   Algorytm:
        1. Pobierz punkty trasy.
        2. Sprawdź warunki (min. ilość punktów).
        3. Uruchom algorytm (np. prosty TSP lub sortowanie po dystansie od punktu startowego).
        4. Zaktualizuj `position` punktów w bazie danych.
        5. Zwróć posortowane punkty.

5.  **Walidacja**:
    *   Czy trasa istnieje i należy do użytkownika?
    *   Czy `route.type == 'manual'`?
    *   Czy liczba punktów >= 2?

6.  **Logowanie**:
    *   Logowanie rozpoczęcia optymalizacji.
    *   Logowanie błędów algorytmu.

7.  **Bezpieczeństwo**:
    *   `IsAuthenticated`.
    *   Weryfikacja właściciela (`user_id`).

8.  **Błędy**:
    *   400: Trasa nie jest `manual` lub za mało punktów.
    *   404: Trasa nie znaleziona.
</analysis>

# API Endpoint Implementation Plan: POST /api/routes/{id}/optimize/

## 1. Przegląd punktu końcowego
Punkt końcowy `POST /api/routes/{id}/optimize/` służy do automatycznego przeorganizowania kolejności punktów na trasie stworzonej ręcznie (`manual`). Ma to na celu znalezienie najbardziej optymalnej drogi (np. najkrótszej) pomiędzy wybranymi punktami. Operacja ta trwale zmienia kolejność punktów w bazie danych dla danej trasy.

## 2. Szczegóły żądania
- **Metoda HTTP**: `POST`
- **Struktura URL**: `/api/routes/{id}/optimize/`
- **Parametry URL**:
  - `id` (wymagane): Unikalny identyfikator trasy.
- **Request Body** (JSON, opcjonalne):
  ```json
  {
    "strategy": "tsp_approx"  // Opcjonalnie: wybór strategii optymalizacji (domyślnie np. najbliższy sąsiad)
  }
  ```

## 3. Wymagane komponenty (Modele, Serializery, Widoki)

### Modele
- `routes.models.Route`: Weryfikacja typu trasy (`route_type`).
- `routes.models.RoutePoint`: Aktualizacja pola `position` po optymalizacji.

### Serializery
- **Input**: `RouteOptimizeInputSerializer` (nowy) - do walidacji parametrów konfiguracyjnych.
- **Output**: `RoutePointSerializer` (istniejący) - do zwrócenia listy punktów.

### Widoki
- `RouteViewSet`: Dodanie nowej akcji `@action(detail=True, methods=['post'])`.

### Serwisy
- `RouteService`: Metoda `optimize_route(route, strategy)`.

## 4. Szczegóły odpowiedzi

### Sukces (200 OK)
Zwraca listę punktów trasy po przeliczeniu kolejności.
```json
[
  {
    "id": 101,
    "place": { ... },
    "position": 0,
    "optimized_position": null
  },
  {
    "id": 105,
    "place": { ... },
    "position": 1,
    "optimized_position": null
  },
  ...
]
```

### Błędy
- **400 Bad Request**:
  - Trasa nie jest typu `manual`.
  - Trasa ma mniej niż 2 punkty.
- **404 Not Found**: Trasa nie istnieje.
- **403 Forbidden**: Brak dostępu do trasy (inny użytkownik).

## 5. Przepływ danych
1.  **Widok (`RouteViewSet.optimize`)**: Odbiera żądanie, sprawdza uprawnienia i waliduje `id`.
2.  **Serializer (`RouteOptimizeInputSerializer`)**: Waliduje opcjonalne parametry konfiguracyjne z body.
3.  **Serwis (`RouteService.optimize_route`)**:
    *   Pobiera instancję `Route`.
    *   Sprawdza reguły biznesowe (`route_type`, liczba punktów).
    *   Pobiera powiązane `RoutePoint`.
    *   Wykonuje logikę sortowania/optymalizacji (na początku prosta implementacja, np. Nearest Neighbor).
    *   Aktualizuje `position` w tabeli `route_points`.
4.  **Widok**: Zwraca zaktualizowaną listę punktów używając `RoutePointSerializer`.

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Wymagany token (JWT/Session) - `IsAuthenticated`.
- **Autoryzacja**: Użytkownik może optymalizować tylko własne trasy. Sprawdzenie `request.user == route.user`.

## 7. Obsługa błędów
- **`ValidationError`** (DRF): Zwracane jako 400, gdy walidacja wejściowa nie powiedzie się.
- **`BusinessLogicException`** (custom): Zwracane jako 400, gdy naruszone są reguły biznesowe (zły typ trasy).
- **Standardowe wyjątki Django**: `DoesNotExist` -> 404.

## 8. Rozważania dotyczące wydajności
- **Transakcje**: Operacja aktualizacji kolejności punktów powinna być atomowa (`transaction.atomic`), aby uniknąć niespójnego stanu w przypadku błędu w połowie zapisu.
- **Bulk Update**: Użycie `RoutePoint.objects.bulk_update()` do zapisania nowych pozycji w jednym zapytaniu SQL, zamiast N zapytań.
- **Algorytm**: Dla małej liczby punktów (np. < 20) proste algorytmy w Pythonie są wystarczające. Dla dużych zbiorów warto rozważyć asynchroniczność (Celery), ale przy obecnych założeniach (route planning) operacja powinna być wystarczająco szybka dla HTTP.

## 9. Etapy wdrożenia

1.  **Stworzenie Serializera Wejściowego**:
    - Utwórz `RouteOptimizeInputSerializer` w `routes/serializers.py`.
2.  **Implementacja Logiki Biznesowej**:
    - W `routes/services.py` dodaj metodę `optimize_route`.
    - Zaimplementuj podstawowy algorytm sortowania (np. zachowaj Start, reszta wg najbliższego sąsiada).
    - Dodaj obsługę błędów biznesowych.
3.  **Aktualizacja Widoku**:
    - W `routes/views.py` w `RouteViewSet` dodaj akcję `optimize`.
    - Podłącz serializer i serwis.
4.  **Testy**:
    - Unit testy dla serwisu (poprawność sortowania, obsługa błędów).
    - Integration testy dla endpointu (sprawdzenie kodów 200, 400, 403).
5.  **Rejestracja URL**:
    - Endpoint będzie automatycznie dostępny dzięki Routerowi DRF (`routes/{id}/optimize/`).
