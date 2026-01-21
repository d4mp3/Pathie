# API Endpoint Implementation Plan: Wylogowanie Użytkownika (`/api/auth/logout/`)

## 1. Przegląd punktu końcowego
Punkt końcowy `POST /api/auth/logout/` służy do bezpiecznego zakończenia sesji użytkownika. Jego głównym celem jest unieważnienie poświadczeń klienta, co w kontekście tego projektu oznacza:
1. Usunięcie tokena autoryzacyjnego API (Token Authentication).
2. Wyczyszczenie sesji Django (Session Authentication) - dla spójności przy dostępie przeglądarkowym/hybrydowym.

Zwraca status `200 OK` po pomyślnym wykonaniu operacji.

## 2. Szczegóły żądania
- **Metoda HTTP**: `POST` (używamy POST zamiast GET, aby uniknąć ataków CSRF i pre-fetchingu przez przeglądarki).
- **Struktura URL**: `/api/auth/logout/`
- **Wymagane Nagłówki**:
  - `Authorization: Token <klucz_tokena>` (lub Cookie sesyjne).
- **Request Body**: Puste.
- **Parametry URL**: Brak.

## 3. Wymagane komponenty (Modele, Serializery, Widoki)

### Modele
- **`rest_framework.authtoken.models.Token`**: Operujemy na istniejącym modelu, usuwając rekord powiązany z użytkownikiem.
- **Brak zmian w schemacie bazy danych.**

### Serializery
- **Brak Serializera Wejściowego**: Endpoint nie przyjmuje danych.
- **Opcjonalnie**: Prosty serializer wyjściowy (np. `{"detail": "Successfully logged out."}`), ale standardowo wystarczy JSON response.

### Widoki
- **`LogoutView`**: Klasa dziedzicząca po `APIView`.
  - Wymaga uwierzytelnienia (`IsAuthenticated`).

## 4. Szczegóły odpowiedzi

### Sukces (`200 OK`)
Potwierdzenie wylogowania.
```json
{
  "detail": "Pomyślnie wylogowano."
}
```

### Błędy
- **`401 Unauthorized`**: Próba wylogowania bez ważnego tokena/sesji.
  ```json
  {
      "detail": "Nie podano danych uwierzytelniających."
  }
  ```

## 5. Przepływ danych
1. **Klient** wysyła żądanie `POST /api/auth/logout/` z nagłówkiem `Authorization`.
2. **Django Middleware / DRF Auth**:
   - Weryfikuje token lub sesję.
   - Ustawia `request.user` i `request.auth` (obiekt Token).
   - Jeśli weryfikacja nie powiedzie się → wraca `401`.
3. **Widok (`LogoutView`)**:
   - Wywołuje logikę biznesową (usunięcie tokena).
   - Wywołuje `django.contrib.auth.logout(request)` (czyszczenie sesji).
4. **Baza Dańych**:
   - `DELETE FROM authtoken_token WHERE key = '...'`.
5. **Odpowiedź**: Zwraca `200 OK`.

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie (Authentication)**: Jest warunkiem koniecznym. Nie można wylogować niezalogowanego użytkownika (zwróci 401).
- **Autoryzacja (Authorization)**: Tylko właściciel tokena może go usunąć (gwarantowane przez mechanizm DRF - `request.user` jest ustalany na podstawie tokena).
- **Zagrożenia**:
  - **CSRF**: Dla sesji przeglądarkowej Django CSRF protection działa. Dla Token Auth CSRF nie ma zastosowania (token w nagłówku).

## 7. Obsługa błędów
- **Brak tokena (`401`)**: Obsługiwane automatycznie przez DRF `IsAuthenticated`.
- **Błąd serwera (`500`)**: Logowany przez standardowy logger Django.

## 8. Rozważania dotyczące wydajności
- **Operacja DELETE**: Jest bardzo szybka (usuwanie po kluczu głównym/indeksie unique).
- **Brak ryzyka N+1**: Operacja dotyczy jednego rekordu.

## 9. Etapy wdrożenia

### Krok 1: Implementacja Logiki (Widok)
Utwórz widok w `pathie/core/views.py`:
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import logout

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Usunięcie tokena DRF
        try:
            # request.auth to instancja Token dla TokenAuthentication
            request.user.auth_token.delete()
        except (AttributeError, Exception):
            # Obsługa sytuacji, gdzie użytkownik nie ma tokena lub używa innej metody
            pass
            
        # Wylogowanie z sesji Django (jeśli używana)
        logout(request)
        
        return Response({"detail": "Pomyślnie wylogowano."}, status=status.HTTP_200_OK)
```

### Krok 2: Konfiguracja URL
Dodaj wpis w `pathie/urls.py` (lub `pathie/core/urls.py`):
```python
from .views import LogoutView

urlpatterns = [
    # ... inne urle
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
]
```

### Krok 3: Weryfikacja
1. Zaloguj się (`POST /api/auth/login/`) i uzyskaj token.
2. Wyślij `POST /api/auth/logout/` z nowym tokenem.
   - Oczekiwane: `200 OK`.
3. Spróbuj użyć starego tokena do pobrania danych (np. `GET /api/routes/`).
   - Oczekiwane: `401 Unauthorized`.
