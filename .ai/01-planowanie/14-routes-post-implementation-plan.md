# API Endpoint Implementation Plan: Route Creation

## 1. Przegląd punktu końcowego
Niniejszy plan opisuje wdrożenie punktu końcowego `POST /api/routes/`. Endpoint ten jest kluczowy dla funkcjonalności aplikacji, umożliwiając użytkownikom inicjowanie nowych tras w dwóch trybach:
1.  **AI Generated**: Automatyczne tworzenie planu wycieczki na podstawie zainteresowań (tagów) i opisu. W fazie MVP proces ten jest realizowany synchronicznie (klient czeka na odpowiedź z wygenerowaną trasą).
2.  **Manual**: Utworzenie pustej trasy, do której użytkownik będzie ręcznie dodawał punkty.

## 2. Szczegóły żądania
-   **Metoda HTTP**: `POST`
-   **Struktura URL**: `/api/routes/`
-   **Wymagane nagłówki**:
    -   `Content-Type: application/json`
    -   `Authorization: Bearer <token>`

### Parametry (Request Body)

Wspólne pole: `route_type` (Enum: `ai_generated`, `manual`).

#### Scenariusz A: AI Generated (`route_type="ai_generated"`)
| Pole | Typ | Wymagane | Opis | Walidacja |
| :--- | :--- | :--- | :--- | :--- |
| `tags` | `List[int]` | **TAK** | Lista ID tagów zainteresowań. | Min: 1, Max: 3 elementy. ID muszą istnieć w tabeli `tags`. |
| `description` | `string` | NIE | Dodatkowy kontekst dla modelu AI (np. "Chcę zwiedzić muzea"). | Max 1000 znaków. |

Przykładowy payload:
```json
{
  "route_type": "ai_generated",
  "tags": [1, 5],
  "description": "Interesuje mnie architektura modernistyczna."
}
```

#### Scenariusz B: Manual (`route_type="manual"`)
| Pole | Typ | Wymagane | Opis | Walidacja |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | NIE | Nazwa własna trasy. | Jeśli brak, backend generuje domyślną (np. "My Custom Trip"). |

Przykładowy payload:
```json
{
  "route_type": "manual",
  "name": "Wycieczka do Krakowa"
}
```

## 3. Wymagane komponenty

### A. Modele (istniejące)
Weryfikacja istnienia modeli w `pathie/core/models.py` (lub odpowiednim module):
-   `Route`
-   `Tag`
-   `RouteTag` (Through model)
-   `AIGenerationLog`

### B. Serializery (`pathie/routes/serializers.py`)

1.  **`RouteCreateSerializer`** (Input):
    -   Implementuje metodę `validate(data)`.
    -   Jeśli `route_type == 'ai_generated'`: sprawdza obecność i liczność pola `tags`.
    -   Jeśli `tags` są podane: weryfikuje istnienie ID w bazie.
    -   Jeśli `route_type != 'ai_generated'` a podano `tags`: zgłasza błąd (lub ignoruje, zależnie od ścisłości API - zalecane zgłaszanie błędu dla czystości).

2.  **`RouteDetailSerializer`** (Output):
    -   Definiuje format odpowiedzi zwracanej klientowi (zagnieżdżone `points`, `place` itp., analogicznie do `GET /api/routes/{id}/`).

### C. Warstwa Logiki Biznesowej (`pathie/routes/services.py`)

Utworzenie serwisu `RouteService` separującego logikę od widoków:

```python
# Pseudo-kod struktury
class RouteService:
    @staticmethod
    def create_route(user, validated_data) -> Route:
        route_type = validated_data.get('route_type')
        
        if route_type == 'ai_generated':
            return RouteService._create_ai_route(user, validated_data)
        else:
            return RouteService._create_manual_route(user, validated_data)

    @staticmethod
    def _create_ai_route(user, data):
        # 1. Utwórz obiekt Route (status=temporary) w transakcji
        # 2. Powiąż tagi (RouteTag)
        # 3. Utwórz AIGenerationLog
        # 4. Wywołaj system AI (OpenRouter/OpenAI) - SYNCHRONICZNIE
        # 5. Zapisz wynikowe punkty (RoutePoints) i opisy (PlaceDescriptions)
        # 6. Zaktualizuj status logu
        return route

    @staticmethod
    def _create_manual_route(user, data):
        # Proste utworzenie obiektu
        return Route.objects.create(...)
```

### D. Widok (`pathie/routes/views.py`)
-   `RouteViewSet` rozszerzający `ModelViewSet`.
-   Nadpisanie metody `create` lub użycie standardowej z podpiętym `RouteCreateSerializer`.
-   Użycie `perform_create` może nie wystarczyć ze względu na skomplikowaną logikę zwrotną, lepiej nadpisać `create` i wywołać Service.

## 4. Szczegóły odpowiedzi

### Sukces (`201 Created`)
Zwraca pełny obiekt utworzonej trasy. Struktura identyczna jak w `GET /api/routes/{id}/`.

```json
{
  "id": 102,
  "name": "Modernist Architecture Tour",
  "status": "temporary",
  "route_type": "ai_generated",
  "created_at": "2024-05-20T10:00:00Z",
  "points": [
    {
      "id": 505,
      "order": 1,
      "place": { "name": "...", "lat": 52.0, "lon": 21.0 },
      "description": { "content": "..." }
    }
    // ...
  ]
}
```

### Błędy
-   **`400 Bad Request`**: Błędy walidacji danych wejściowych.
    ```json
    { "tags": ["Ensure this field has at least 1 elements."] }
    ```
    lub
    ```json
    { "non_field_errors": ["Tags are required for AI generation."] }
    ```
-   **`401 Unauthorized`**: Brak tokena JWT.
-   **`503 Service Unavailable`**: Jeśli zewnętrzny serwis AI nie odpowiada (opcjonalne, może być 500 w MVP).

## 5. Przepływ danych

1.  **Request**: Użytkownik wysyła POST z tagami (dla AI).
2.  **API Layer**: Django weryfikuje Token JWT.
3.  **Serializer**:
    -   Sprawdza typy danych.
    -   `validate()`: Logika warunkowa dla `route_type`.
4.  **Service Layer (wewnątrz transakcji `atomic`)**:
    -   Tworzony jest nagłówek Trasy (`Route`).
    -   Dla AI:
        -   Budowany jest prompt na podstawie tagów.
        -   Wysłanie żądania do LLM.
        -   Odbiór JSON z listą miejsc.
        -   Iteracja po miejscach: Sprawdzenie czy miejsce istnieje w tabeli `Places` (po `osm_id`/`wikipedia_id`), jeśli nie -> utworzenie.
        -   Utworzenie `RoutePoint` łączącego `Route` i `Place`.
        -   Utworzenie `PlaceDescription`.
5.  **Response**: Serializacja w pełni utworzonej struktury i zwrot do klienta.

## 6. Względy bezpieczeństwa
-   **Uprawnienia**: Klasa `IsAuthenticated`.
-   **Rate Limiting**: Zalecane użycie `UserRateThrottle` specyficznie dla tego endpointu (np. "10/hour"), aby uniknąć wysokich kosztów API AI.
-   **Sanityzacja**: Chociaż DRF chroni przed SQL Injection, generowane przez AI treści (opisy) powinny być traktowane jako zaufane (pochodzą z naszego promptu), ale warto o tym pamiętać przy wyświetlaniu (klient webowy powinien escapować HTML).

## 7. Obsługa błędów
-   **AI Timeout**: Wywołania do LLM mogą trwać długo (>30s). Wdrożenie powinno zakładać rozsądny timeout (np. 60s) w konfiguracji Gunicorn/Nginx. W przypadku timeoutu, tranzakcja DB powinna zostać wycofana.
-   **Błędy Providera AI**: Logowanie błędów do Sentry/Console i zwracanie użytkownikowi komunikatu "AI service temporary unavailable".

## 8. Rozważania dotyczące wydajności
-   **Database Transactions**: Cały proces tworzenia trasy AI musi być jedną transakcją (`transaction.atomic()`). Zapobiegnie to powstawaniu "sierot" (tras bez punktów) w przypadku błędu w połowie generowania.
-   **OpenStreetMap Lookup**: Jeśli sprawdzamy miejsca w zewnętrznym serwisie geocodingu, wpłynie to na czas. W MVP zalecane poleganie tylko na danych zwróconych przez LLM lub lokalnej bazie `Places` jeśli już mamy dane.

## 9. Etapy wdrożenia
Kroki dla programisty:

1.  **Przygotowanie Modeli**: Upewnij się, że relacje `Route` <-> `Tag` i `Route` <-> `Place` są poprawne.
2.  **Mock AI Service**: Zaimplementuj klasę `AIService` z metodą `generate(tags)`, która zwraca sztywne dane testowe (bez dzwonienia do API). Pozwoli to przetestować flow bez kosztów i latencji.
3.  **Implementacja Serializera**: Napisz `RouteCreateSerializer` z walidacją `route_type`.
4.  **Implementacja Widoku i Serwisu**:
    -   Stwórz `RouteService.create_route`.
    -   Podepnij pod widok.
5.  **Testy Manualne**: Sprawdź tworzenie trasy "Manual" (powinna być pusta) i "AI" (powinna mieć mockowe punkty).
6.  **Integracja LLM**: Podmień mock w `AIService` na prawdziwe wywołanie (np. LangChain lub bezpośrednio `openai`/`requests`).
7.  **Rate Limiting**: Dodaj konfigurację throttlingu w `settings.py`.
