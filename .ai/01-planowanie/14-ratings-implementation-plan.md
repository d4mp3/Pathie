# API Endpoint Implementation Plan: POST /api/ratings/

## 1. Przegląd punktu końcowego
Punkt końcowy `POST /api/ratings/` służy do dodawania lub aktualizowania (UPSERT) oceny użytkownika dla trasy (`route`) lub opisu miejsca (`place_description`). Umożliwia użytkownikom wyrażanie opinii (pozytywnej lub negatywnej) na temat wygenerowanych treści.

## 2. Szczegóły żądania
- **Metoda HTTP**: `POST`
- **Struktura URL**: `/api/ratings/`
- **Parametry URL**: Brak
- **Request Body (JSON)**:
  - **Wymagane**:
    - `rating_type`: string, wartości `'route'` lub `'place_description'`.
    - `rating_value`: integer, wartości `1` (pozytywna) lub `-1` (negatywna).
    - *Warunkowo*:
      - Jeśli `rating_type` to `'route'`: `route_id` (integer) jest wymagane.
      - Jeśli `rating_type` to `'place_description'`: `place_description_id` (integer) jest wymagane.

  Przykład (ocena trasy):
  ```json
  {
    "rating_type": "route",
    "rating_value": 1,
    "route_id": 101,
    "place_description_id": null
  }
  ```

## 3. Wymagane komponenty (Modele, Serializery, Widoki)

### Modele (`pathie/core/models/rating.py`)
- Wykorzystanie istniejącego modelu `Rating`.
- Pola kluczowe: `user` (FK), `rating_type`, `rating_value`, `route` (FK), `place_description` (FK).
- Model powinien wspierać unikalność pary `(user, target)` (logicznie obsłużone przez `update_or_create`).

### Serializery (`pathie/core/serializers.py`)
- **`RatingSerializer`**:
  - Pola: `id`, `rating_type`, `rating_value`, `route_id`, `place_description_id`.
  - **Walidacja**:
    - `validate_rating_value`: Musi być `1` lub `-1`.
    - `validate`: Sprawdzenie spójności `rating_type` z podanym ID (np. jeśli `rating_type='route'`, to `route_id` musi być obecne).
    - `user` będzie pobierany z kontekstu żądania (`request.user`), nie z body.

### Widoki (`pathie/core/views.py`)
- **`RatingViewSet`** (lub `APIView`):
  - Metoda `create`: Obsłuży logikę UPSERT.
  - Zamiast standardowego `serializer.save()`, użyjemy logiki `update_or_create` (patrz sekcja Przepływ danych).

## 4. Szczegóły odpowiedzi
- **Sukces (Utworzono/Zaktualizowano)**:
  - Kod: `201 Created` (dla utworzenia) lub `200 OK` (dla aktualizacji).
  - Body: Zserializowany obiekt oceny (np. potwierdzenie ID i wartości).
- **Błąd**:
  - Kod: `400 Bad Request` (Błędy walidacji, np. brak wymaganych pól, niepoprawna wartość oceny).

## 5. Przepływ danych
1. **Klient**: Wysyła żądanie `POST /api/ratings/` z tokenem JWT.
2. **Widok (`RatingViewSet.create`)**:
   - Sprawdza uprawnienia (`IsAuthenticated`).
   - Przekazuje dane do `RatingSerializer` w celu walidacji wstępnej (formaty, typy).
3. **Logika Biznesowa (wewnątrz `perform_create` lub Widoku)**:
   - Pobiera `user` z `request.user`.
   - Na podstawie `rating_type` określa cel (`route` lub `place_description`).
   - Wywołuje `Rating.objects.update_or_create`:
     - **Lookup parameters**: `user`, oraz `route_id` LUB `place_description_id` (zależnie od typu).
     - **Defaults**: `rating_value`, `rating_type`.
4. **Baza Danych**: Wykonuje zapytanie INSERT lub UPDATE.
5. **Odpowiedź**: Widok zwraca zserializowany obiekt z odpowiednim kodem statusu.

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Wymagany nagłówek `Authorization: Bearer <token>`.
- **Uprawnienia**: Klasa `IsAuthenticated`. Tylko zalogowani użytkownicy mogą oceniać.
- **Dostęp do zasobów**: Upewnienie się, że oceniany zasób (trasa/opis) istnieje (wymuszone przez FK w bazie, ale walidacja serializera powinna to wyłapać wcześniej jako `ValidationError`).
- **Rate Limiting**: Standardowe limity API, aby zapobiec spamowaniu ocenami (opcjonalnie).

## 7. Obsługa błędów
- **Błędy walidacji (400)**:
  - Brak `route_id` przy `rating_type='route'`.
  - `rating_value` inne niż {-1, 1}.
  - Próba oceny nieistniejącego obiektu (Foreign Key constraint violation / `DoesNotExist`).
- **Nieautoryzowany (401)**: Brak lub nieprawidłowy token.
- **Błąd serwera (500)**: Nieoczekiwane błędy bazy danych.

## 8. Rozważania dotyczące wydajności
- **Indeksy**: Upewnić się, że istnieją indeksy na polach FK (`user_id`, `route_id`, `place_description_id`) dla szybkiego wyszukiwania przy `update_or_create`.
- **N+1**: Przy tworzeniu pojedynczej oceny problem N+1 jest mało prawdopodobny, ale warto o nim pamiętać przy ewentualnym pobieraniu listy ocen (użyć `select_related`).

## 9. Etapy wdrożenia

1. **Aktualizacja Serializera (`pathie/core/serializers.py`)**:
   - Stworzenie `RatingSerializer` z polami `rating_type`, `rating_value`, `route_id`, `place_description_id`.
   - Dodanie metody `validate` do sprawdzania warunkowych wymagań ID.

2. **Implementacja Widoku (`pathie/core/views.py`)**:
   - Dodanie `RatingViewSet` z dziedziczeniem po `viewsets.GenericViewSet` (lub `ModelViewSet`, ale blokując inne metody jeśli niepotrzebne).
   - Nadpisanie metody `create` (z `mixins.CreateModelMixin`) lub implementacja własnej, aby obsłużyć logikę `update_or_create`.
   - Obsługa rozróźnienia kodów `201` vs `200` (zależnie od flagi `created` z `update_or_create`).

3. **Konfiguracja URL (`pathie/core/urls.py` lub `pathie/urls.py`)**:
   - Rejestracja endpointu `/api/ratings/` w routerze.

4. **Testy (Manualne/Automatyczne)**:
   - Test tworzenia nowej oceny (201).
   - Test aktualizacji istniejącej oceny (zmiana z 1 na -1) (200).
   - Test walidacji "cross-field" (typ vs ID) (400).
