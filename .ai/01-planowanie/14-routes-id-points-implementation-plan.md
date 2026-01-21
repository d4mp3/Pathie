<analysis>
### Analiza Wdrożenia Endpointu POST `/api/routes/{id}/points/`

1.  **Kluczowe punkty specyfikacji:**
    *   **Cel:** Dodanie nowego punktu (miejsca) do istniejącej trasy manualnej.
    *   **Automatyzacja:** Jeśli miejsce (`Place`) nie istnieje, system ma je utworzyć na podstawie danych wejściowych (lookup po `osm_id`).
    *   **Metoda:** POST.
    *   **URL:** `/api/routes/{id}/points/`.

2.  **Parametry:**
    *   **Path:** `id` (ID trasy).
    *   **Body (JSON):** Obiekt `place` zawierający:
        *   `name` (wymagane)
        *   `lat`, `lon` (wymagane)
        *   `osm_id` (opcjonalne, zalecane do deduplikacji)
        *   `address` (opcjonalne)
        *   Inne (np. `wikipedia_id`) - w oparciu o model `Place` (choć `PlaceInputSerializer` może wymagać aktualizacji).

3.  **Serializery:**
    *   **Wejściowy:** `RoutePointCreateSerializer` (już istnieje w `pathie/core/serializers.py`). Zawiera `PlaceInputSerializer`.
        *   *Uwaga:* Należy zweryfikować, czy `PlaceInputSerializer` obsługuje `wikipedia_id`, jeśli jest to wymagane (model to ma). Obecny kod nie widzi tego pola w input serializerze. Dodamy to jako ulepszenie.
    *   **Wyjściowy:** `RoutePointSerializer` (istnieje). Zawiera pełne zagnieżdżenie `Place` i `PlaceDescription`.

4.  **Logika Biznesowa:**
    *   **Lokalizacja:** Głównie w `RoutePointCreateSerializer.create()` (już zaimplementowane: lookup miejsca, tworzenie, obliczanie pozycji).
        *   *Brakuje:* Walidacji typu trasy (`manual`) oraz limitu punktów w `validate` lub w widoku. Zalecane umieszczenie w serializerze lub widoku przed zapisem.
    *   **Widok:** Akcja w `RouteViewSet` (np. `@action(detail=True, methods=['post'])`).

5.  **Walidacja:**
    *   Sprawdzenie czy trasa istnieje i należy do użytkownika (w widoku `get_object`).
    *   Sprawdzenie typu trasy (`route_type == 'manual'`).
    *   Sprawdzenie limitu punktów (np. max 50).
    *   Walidacja danych geograficznych (w serializerze).

6.  **Logowanie i Bezpieczeństwo:**
    *   Standardowe logowanie błędów.
    *   Uwierzytelnianie: `IsAuthenticated`.
    *   Autoryzacja: Użytkownik musi być właścicielem trasy.

7.  **Scenariusze błędów:**
    *   404: Trasa nie istnieje.
    *   403: Brak dostępu (inna osoba).
    *   400: Limit punktów osiągnięty, Trasa nie jest manualna, Błędne dane wejściowe.
</analysis>

# API Endpoint Implementation Plan: POST `/api/routes/{id}/points/`

## 1. Przegląd punktu końcowego
Plan dotyczy wdrożenia endpointu umożliwiającego dodawanie nowych punktów (miejsc) do istniejącej, manualnej trasy użytkownika. System automatycznie obsłuży tworzenie nowych rekordów `Place` w bazie danych, jeśli dane miejsce jeszcze nie istnieje (na podstawie `osm_id`), lub wykorzysta istniejące, a następnie powiąże je z trasą poprzez `RoutePoint`.

## 2. Szczegóły żądania
- **Metoda HTTP**: `POST`
- **Struktura URL**: `/api/routes/{id}/points/`
- **Parametry**:
  - **Path (Wymagane)**: `id` (ID trasy, Integer)
- **Request Body**:
  ```json
  {
    "place": {
      "name": "Palace of Culture",
      "lat": 52.231,
      "lon": 21.006,
      "osm_id": 123456,
      "address": "Plac Defilad 1",
      "wikipedia_id": "pl:Pałac Kultury i Nauki"
    }
  }
  ```
  - **Pola `place`**:
    - `name` (string, required)
    - `lat` (float, required)
    - `lon` (float, required)
    - `osm_id` (int/bigint, optional)
    - `address` (string, optional)
    - `wikipedia_id` (string, optional - do dodania w serializerze)

## 3. Wymagane komponenty
- **Widok**: `RouteViewSet` w `pathie/core/views.py`.
  - Nowa metoda/akcja: `add_point` (mapowana na `points/`).
- **Serializery**: `pathie/core/serializers.py`
  - `PlaceInputSerializer`: Aktualizacja o pole `wikipedia_id` (opcjonalne).
  - `RoutePointCreateSerializer`: Istniejący serializer do obsługi logiki tworzenia. Wymaga dodania walidacji kontekstowej (limit punktów, typ trasy).
  - `RoutePointSerializer`: Używany do zwrócenia sformatowanej odpowiedzi.
- **Uprawnienia**: `IsAuthenticated`, weryfikacja własności trasy (`owner`).

## 4. Szczegóły odpowiedzi
- **Status 201 Created**: Pomyślnie dodano punkt.
- **Payload**:
  ```json
  {
    "id": 101,
    "position": 5,
    "place": {
      "id": 55,
      "name": "Palace of Culture",
      "lat": 52.231,
      "lon": 21.006,
      ...
    },
    "description": null
  }
  ```

## 5. Przepływ danych
1.  **Request**: Klient wysyła żądanie POST z danymi miejsca.
2.  **Widok (`RouteViewSet`)**:
    *   Pobiera trasę na podstawie `id` i autoryzuje użytkownika.
    *   Sprawdza, czy trasa jest typu `manual`.
    *   Sprawdza, czy nie przekroczono limitu punktów dla trasy (np. max 50).
3.  **Serializer (`RoutePointCreateSerializer`)**:
    *   Waliduje dane wejściowe `place`.
    *   **Metoda `create`**:
        *   Szuka istniejącego `Place` po `osm_id` (lub `wikipedia_id` jeśli podano).
        *   Jeśli nie istnieje, tworzy nowe `Place`.
        *   Oblicza kolejną pozycję (`max(position) + 1`).
        *   Tworzy i zwraca `RoutePoint`.
4.  **Odpowiedź**: Widok serializuje utworzony obiekt używając `RoutePointSerializer` i zwraca kod 201.

## 6. Względy bezpieczeństwa
-   **Uwierzytelnianie**: Endpoint dostępny tylko dla zalogowanych użytkowników (`IsAuthenticated`).
-   **Autoryzacja (Object Level)**: Użytkownik może modyfikować tylko własne trasy. Próba modyfikacji trasy innego użytkownika zwróci `404 Not Found` (standard Django filtra queryset) lub `403 Forbidden`.
-   **Walidacja typu trasy**: Blokada edycji tras o typie `ai_generated`, chyba że logika biznesowa dopuszcza ich edycję jako manualną po konwersji (na ten moment specyfikacja mówi: "Adds a new point to a manual route").
-   **Input Validation**: Walidacja koordynatów geograficznych (`lat`: -90 do 90, `lon`: -180 do 180).

## 7. Obsługa błędów
-   **404 Not Found**: Trasa o podanym ID nie istnieje lub nie należy do użytkownika.
-   **400 Bad Request**:
    -   `{"detail": "Cannot add points to AI generated route."}` - próba edycji trasy AI.
    -   `{"detail": "Max points limit reached."}` - przekroczenie limitu punktów.
    -   Błędy walidacji danych wejściowych (np. brak nazwy, błędne współrzędne).
-   **500 Internal Server Error**: Błąd bazy danych lub inna nieoczekiwana awaria.

## 8. Rozważania dotyczące wydajności
-   **N+1 Queries**: Serializer wyjściowy `RoutePointSerializer` korzysta z `place` i `description`. Przy tworzeniu pojedynczego punktu nie jest to krytyczne, ale należy pamiętać o `select_related('place', 'description')` przy pobieraniu instancji do odpowiedzi, jeśli to możliwe, lub po prostu odczytać dane z obiektu stworzonego w pamięci.
-   **Indeksy**: Wyszukiwanie `Place` po `osm_id` jest szybkie dzięki `unique=True` (implikuje indeks).

## 9. Etapy wdrożenia

### Krok 1: Aktualizacja Serializerów
W pliku `pathie/core/serializers.py`:
1.  Zaktualizuj `PlaceInputSerializer`, dodając pole `wikipedia_id = serializers.CharField(..., required=False)`.
2.  Zaktualizuj `RoutePointCreateSerializer` lub logikę widoku:
    *   Upewnij się, że logiczna obsługa `wikipedia_id` jest dodana przy `get_or_create` miejsca.

### Krok 2: Implementacja Widoku
W pliku `pathie/core/views.py`:
1.  Stwórz `RouteViewSet` dziedziczący po `ModelViewSet` (lub odpowiednich mixinach).
2.  Zdefiniuj `queryset` (filtrowanie per user) i `serializer_class`.
3.  Dodaj metodę `@action(detail=True, methods=['post'], url_path='points')`.
    *   Pobierz trasę: `self.get_object()`.
    *   Walidacja typu (`check logic`).
    *   Walidacja limitu (`route.points.count()`).
    *   Inicjalizacja `RoutePointCreateSerializer` z `data=request.data` i kontekstem.
    *   Zapis: `serializer.save(route=route)`.
    *   Zwrot odpowiedzi: `RoutePointSerializer(result).data`, status 201.

### Krok 3: Konfiguracja URL
W pliku `pathie/core/urls.py` (lub `pathie/urls.py`):
1.  Zarejestruj `RouteViewSet` używając routera DRF.

### Krok 4: Testy
To zadanie wykracza poza ten plan, ale należy zweryfikować:
-   Dodanie punktu do trasy manualnej (sukces, nowe miejsce).
-   Dodanie punktu z istniejącym `osm_id` (sukces, ponowne użycie miejsca).
-   Próba dodania do trasy AI (błąd 400).
-   Próba dodania do nie swojej trasy (błąd 404).
