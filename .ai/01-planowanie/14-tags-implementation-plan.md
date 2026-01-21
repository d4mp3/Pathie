# API Endpoint Implementation Plan: Tags List

## 1. Przegląd punktu końcowego
Celem tego endpointu jest dostarczenie listy dostępnych tagów zainteresowań (`tags`), które mogą być wykorzystane przez użytkownika podczas generowania tras. Endpoint zwraca listę obiektów zawierających identyfikator, nazwę, opis oraz status aktywności tagu.

## 2. Szczegóły żądania
- **Metoda HTTP**: `GET`
- **Struktura URL**: `/api/tags/`
- **Parametry**:
  - **Wymagane**: Brak.
  - **Opcjonalne**: Brak (wg specyfikacji), ale warto rozważyć standardową paginację, jeśli liczba tagów będzie duża. W MVP zakładamy zwrócenie wszystkich aktywnych tagów.
- **Request Body**: Brak.

## 3. Wymagane komponenty (Modele, Serializery, Widoki)

### Modele
- **`Tag`**: Model już istnieje w `pathie.core.models.tag`. Nie wymaga modyfikacji.
  - Pola: `id`, `name`, `description`, `is_active`, `priority`.

### Serializery
- **`TagSerializer`**: Serializer już istnieje w `pathie.core.serializers`.
  - Pola: `['id', 'name', 'description', 'is_active']`.
  - Typ: `ModelSerializer`.
  - Uwaga: Upewnić się, że serializer jest zgodny ze specyfikacją (zwraca dokładnie te pola).

### Widoki
- **`TagListView`**: Nowy widok w `pathie.core.views`.
  - Typ: `generics.ListAPIView` (z `rest_framework`).
  - Queryset: `Tag.objects.filter(is_active=True)` - zwracamy tylko aktywne tagi, które są "dostępne" do trasy. (Chociaż specyfikacja pokazuje pole `is_active` w odpowiedzi, co może sugerować zwracanie wszystkich. Bezpieczniej jest zwrócić tylko `is_active=True` dla "available interest tags", chyba że front-end wymaga widoku wyłączonych tagów). **Decyzja**: Zwracamy wszystkie tagi posortowane po priorytecie (`-priority`, `name`), aby klient mógł decydować o wyświetlaniu, lub (zgodnie z "available") filtrować po `is_active=True`. W tym planie przyjmiemy filtrowanie `is_active=True` jako domyślne zachowanie dla "dostępnych" tagów, ale pole `is_active` w odpowiedzi pozostanie `true`.
  - Permission classes: `IsAuthenticated` (zakładamy, że generowanie tras jest dla zalogowanych) lub `AllowAny` (jeśli tagi są publiczne). Ze względów bezpieczeństwa domyślnie `IsAuthenticated`.

## 4. Szczegóły odpowiedzi
- **Kod sukcesu**: `200 OK`
- **Struktura JSON**:
  ```json
  [
    {
      "id": 1,
      "name": "History",
      "description": "Historical landmarks and museums",
      "is_active": true
    },
    ...
  ]
  ```

## 5. Przepływ danych
1.  **Klient** wysyła żądanie `GET /api/tags/`.
2.  **Django URL Resolver** kieruje żądanie do `TagListView`.
3.  **TagListView** sprawdza uprawnienia (`IsAuthenticated`).
4.  **TagListView** pobiera dane z bazy: `Tag.objects.filter(is_active=True).order_by('-priority', 'name')`.
5.  **TagSerializer** przekształca obiekty `Tag` na format JSON.
6.  **Serwer** zwraca odpowiedź JSON z kodem `200 OK`.

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Wymagane jest, aby użytkownik był sytemie (np. token JWT/Session), jeśli endpoint ma być chroniony. Użyj `IsAuthenticated`.
- **Autoryzacja**: Tylko odczyt (`GET`). Brak możliwości modyfikacji danych przez ten endpoint.
- **Walidacja**: Brak danych wejściowych do walidacji.

## 7. Obsługa błędów
- **500 Internal Server Error**: W przypadku błędu połączenia z bazą danych lub błędu serwera.
- **401 Unauthorized**: Jeśli użytkownik nie jest zalogowany (jeśli używamy `IsAuthenticated`).

## 8. Rozważania dotyczące wydajności
- **Indeksowanie**: Tabela `tags` ma być mała (słownikowa), więc pełny skan nie jest problemem.
- **Ilość danych**: Jeśli liczba tagów wzrośnie > 100, należy włączyć paginację (`PageNumberPagination`). Na start lista może być niepaginowana (zwraca listę `[...]` a nie obiekt paginowany `{count, results...}` - uwaga: API Standard Django włącza paginację domyślnie jeśli jest w settings. Aby zwrócić czystą listę `[...]` jak w specyfikacji, należy wyłączyć paginację dla tego widoku (`pagination_class = None`).
- **Caching**: Tagi zmieniają się rzadko. Można rozważyć cache (np. Redis) na poziomie widoku na 1h.

## 9. Etapy wdrożenia

### Krok 1: Weryfikacja Modelu i Serializera
- Sprawdź `pathie/core/models/tag.py` czy model `Tag` jest poprawny.
- Sprawdź `pathie/core/serializers.py` czy `TagSerializer` jest poprawny i zawiera wymagane pola.

### Krok 2: Implementacja Widoku
- Edytuj `pathie/core/views.py`.
- Dodaj importy:
  ```python
  from rest_framework import generics
  from rest_framework.permissions import IsAuthenticated, AllowAny
  from .models.tag import Tag
  from .serializers import TagSerializer
  ```
- Utwórz klasę `TagListView(generics.ListAPIView)`:
  - Ustaw `queryset = Tag.objects.filter(is_active=True).order_by('-priority', 'name')`
  - Ustaw `serializer_class = TagSerializer`
  - Ustaw `pagination_class = None` (aby zwrócić płaską listę array, zgodnie z przykładem w specyfikacji)
  - Ustaw `permission_classes = [IsAuthenticated]`

### Krok 3: Konfiguracja URL
- Utwórz plik `pathie/core/urls.py` (jeśli nie istnieje).
- Zdefiniuj `urlpatterns`:
  ```python
  from django.urls import path
  from .views import TagListView

  urlpatterns = [
      path('tags/', TagListView.as_view(), name='tag-list'),
  ]
  ```
- Dołącz `pathie/core/urls.py` do głównego `pathie/urls.py` (używając `include`).

### Krok 4: Testy Manualne / Automatyczne
- Uruchom serwer (`python manage.py runserver`).
- Wykonaj żądanie GET na `/api/tags/` używając Postman/curl (z tokenem auth).
- Zweryfikuj, czy odpowiedź to tablica JSON z tagami.
