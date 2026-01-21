# API Endpoint Implementation Plan: Delete Route

## 1. Przegląd punktu końcowego
Ten plan opisuje wdrożenie punktu końcowego `DELETE /api/routes/{id}/`, który umożliwia użytkownikom usuwanie stworzonych przez siebie tras. Operacja ta usunie trasę oraz kaskadowo wszystkie powiązane z nią zasoby (punkty trasy, opisy, oceny, logi AI), zachowując jednak same definicje miejsc (`places`).

## 2. Szczegóły żądania
- **Metoda HTTP**: `DELETE`
- **Struktura URL**: `/api/routes/{id}/`
- **Parametry**:
  - **Wymagane (Path)**: `id` (integer) - Unikalny identyfikator trasy do usunięcia.
  - **Opcjonalne**: Brak.
- **Request Body**: Brak.

## 3. Wymagane komponenty (Modele, Serializery, Widoki)
- **Widok**: `RouteViewSet` (rozszerzenie istniejącego ViewSetu o metodę `destroy` lub wykorzystanie domyślnej implementacji `ModelViewSet`).
- **Uprawnienia**:
  - `IsAuthenticated`: Tylko zalogowani użytkownicy mogą usuwać trasy.
  - Właścicielstwo: Użytkownik może usunąć tylko własną trasę (`user_id` musi pasować do `request.user.id`).
- **Modele**:
  - `Route` (operacja usuwania).
  - Powiązane modele usuwane kaskadowo: `RoutePoint`, `PlaceDescription` (przez `RoutePoint`), `Rating` (dla trasy), `AIGenerationLog`, `RouteTag`.

## 4. Szczegóły odpowiedzi
- **Sukces**:
  - **Kod statusu**: `204 No Content`
  - **Body**: Puste.
- **Błędy**:
  - `401 Unauthorized` - Brak lub nieprawidłowy token.
  - `404 Not Found` - Trasa o podanym ID nie istnieje lub należy do innego użytkownika.
  - `500 Internal Server Error` - Błąd serwera podczas usuwania.

## 5. Przepływ danych
1. **Odbiór żądania**: Django odbiera żądanie `DELETE` z parametrem `id`.
2. **Uwierzytelnienie**: Weryfikacja tokena użytkownika.
3. **Pobranie zasobu (Queryset Filter)**:
   - Zapytanie do bazy: `SELECT * FROM routes WHERE id = {id} AND user_id = {request.user.id}`.
   - Jeśli wynik jest pusty -> Zwróć `404 Not Found`.
4. **Usunięcie (Model delete)**:
   - Wywołanie metody `.delete()` na instancji modelu `Route`.
5. **Kaskada bazy danych**:
   - Baza danych (PostgreSQL) automatycznie usuwa powiązane rekordy dzięki klauzulom `ON DELETE CASCADE`:
     - `route_tags` (tagi przypisane do trasy).
     - `route_points` (punkty trasy).
       - Kaskadowo: `place_descriptions` (opisy punktów).
     - `ratings` (oceny trasy).
     - `ai_generation_logs` (logi generowania).
   - **Uwaga**: Rekordy w tabeli `places` pozostają nienaruszone.
6. **Odpowiedź**: Zwróć `204 No Content`.

## 6. Względy bezpieczeństwa
- **Kontrola dostępu (Authorization)**: Kluczowe jest zapewnienie, że użytkownik nie może usunąć trasy innego użytkownika. Mechanizm filtrowania `datasetu` w DRF (np. `get_queryset` zwracający `Route.objects.filter(user=self.request.user)`) skutecznie rozwiązuje ten problem, zwracając `404` dla prób dostępu do cudzych zasobów, co jest bezpieczniejszą praktyką niż `403` (nie ujawnia istnienia zasobu).
- **CSRF**: W przypadku użycia sesji (jeśli dotyczy), wymagana ochrona CSRF. Przy autoryzacji tokenem (JWT/Token) ryzyko jest mniejsze, ale standardowe zabezpieczenia DRF powinny być aktywne.

## 7. Obsługa błędów
- **DoesNotExist (404)**: Standardowa obsługa przez DRF w przypadku braku obiektu w `queryset`.
- **Błędy Bazy Danych (IntegrityError)**: Choć mało prawdopodobne przy standardowym usuwaniu, należy być gotowym na przechwycenie wyjątków bazy danych (np. jeśli inne procesy blokują wiersze) i zwrócenie `500` lub ponowienie próby.

## 8. Rozważania dotyczące wydajności
- **Transakcyjność**: Usuwanie złożonych struktur (trasa + wiele punktów + opisy) powinno być atomowe. W Django domyślnie żądania HTTP mogą być objęte transakcją (`ATOMIC_REQUESTS = True`), co jest zalecane.
- **Czas wykonania**: Przy bardzo dużych drzewach zależności (np. trasa z tysiącem punktów) usuwanie może chwilę potrwać. W obecnej skali (do ~20-30 punktów) operacja będzie natychmiastowa.

## 9. Etapy wdrożenia

1. **Aktualizacja ViewSetu (`views.py`)**:
   - Upewnij się, że `RouteViewSet` dziedziczy po `mixins.DestroyModelMixin` lub `viewsets.ModelViewSet`.
   - Zweryfikuj metodę `get_queryset`, aby filtrowała trasy po `self.request.user`.

   ```python
   # Przykład logiczny w views.py
   class RouteViewSet(viewsets.ModelViewSet):
       permission_classes = [IsAuthenticated]
       # ...
       def get_queryset(self):
           return Route.objects.filter(user=self.request.user)
   ```

2. **Weryfikacja Serializera (`serializers.py`)**:
   - Dla metody DELETE serializer nie jest bezpośrednio używany do walidacji danych wejściowych, ale upewnij się, że nie ma logiki blokującej w samym modelu.

3. **Testy Manualne (Postman/Curl)**:
   - Próba usunięcia istniejącej trasy (oczekiwane 204).
   - Próba usunięcia nieistniejącej trasy (oczekiwane 404).
   - Próba usunięcia trasy innego użytkownika (oczekiwane 404).
   - Weryfikacja w bazie danych czy powiązane `route_points` zniknęły, a `places` pozostały.

4. **Testy Automatyczne (Pytest)**:
   - Test jednostkowy sprawdzający usuwanie i kaskadowość (czy linked objects są usuwane).
   - Test sprawdzający izolację użytkowników.
