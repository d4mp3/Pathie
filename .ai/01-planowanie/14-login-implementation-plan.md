# Plan Implementacji Endpointu API: Login

## 1. Przegląd punktu końcowego
Celem tego endpointu jest umożliwienie użytkownikom uwierzytelnienia się za pomocą adresu e-mail i hasła. W odpowiedzi system generuje i zwraca token autoryzacyjny, który będzie używany w nagłówkach kolejnych żądań do API (Token Authentication).

## 2. Szczegóły żądania
- **Metoda HTTP**: `POST`
- **URL**: `/api/auth/login/`
- **Wymagane parametry (Body - JSON)**:
  - `email`: (string) Adres e-mail użytkownika.
  - `password`: (string) Hasło użytkownika.
- **Opcjonalne parametry**: Brak.

Przykład żądania:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

## 3. Szczegóły odpowiedzi
- **Sukces (200 OK)**:
  - Zwraca klucz tokenu.
  - Struktura: `{"key": "token_string"}`
- **Błąd (400 Bad Request)**:
  - Nieprawidłowe dane wejściowe (np. brak pola, zły format e-mail).
  - Nieprawidłowe dane logowania (zgodnie ze specyfikacją błąd logowania zwraca 400, choć standardowo czasem stosuje się 401).

Przykład odpowiedzi (Sukces):
```json
{
  "key": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

## 4. Wymagane komponenty

### A. Biblioteki zewnętrzne
- **Django REST Framework (DRF)**: Do obsługi serializacji i widoków API.
- **django-cors-headers**: (Opcjonalnie, ale zalecane) Do obsługi Cross-Origin Resource Sharing, jeśli frontend jest oddzielny.

### B. Modele (`apps/core/models.py`)
- Standardowy model użytkownika (`django.contrib.auth.models.User`).
- `rest_framework.authtoken.models.Token` (model dostarczany przez DRF).

### C. Serializery (`apps/api/serializers.py`)
1.  **`LoginSerializer`**:
    - Pola: `email`, `password`.
    - Walidacja: Sprawdzenie formatu e-mail, obecności pól.
    - Metoda `validate`: Weryfikacja poświadczeń (sprawdzenie czy użytkownik istnieje i hasło pasuje). Logika logowania oparta na e-mailu (kustomizacja, ponieważ domyślne Django używa `username`).

### D. Widoki (`apps/api/views.py`)
1.  **`LoginAPIView`**:
    - Typ: `APIView` lub `GenericAPIView`.
    - Logika: Odbiera dane, uruchamia serializer, generuje lub pobiera token (`Token.objects.get_or_create`), zwraca odpowiedź w formacie `{"key": "..."}`.

## 5. Przepływ danych
1.  **Klient**: Wysyła żądanie `POST /api/auth/login/` z JSON-em (`email`, `password`).
2.  **URLConf**: Przekierowuje żądanie do `LoginAPIView`.
3.  **Widok (View)**: Przekazuje dane do `LoginSerializer`.
4.  **Serializer**:
    - Waliduje format danych.
    - Wyszukuje użytkownika po `email` (`User.objects.filter(email=email).first()`).
    - Sprawdza hasło (`user.check_password()`).
    - Zgłasza błąd walidacji, jeśli dane są błędne.
5.  **Widok (View)**:
    - Jeśli walidacja pomyślna: Pobiera użytkownika z `validated_data`.
    - **Baza Danych**: Pobiera lub tworzy token dla użytkownika w tabeli `authtoken_token`.
    - Zwraca odpowiedź JSON z kodem 200.
    - Jeśli walidacja nieudana: Zwraca błędy z kodem 400.

## 6. Względy bezpieczeństwa
- **HTTPS**: Komunikacja musi być szyfrowana.
- **Bezpieczeństwo haseł**: Hasła nigdy nie są zwracane w odpowiedzi ani logowane otwartym tekstem. Walidacja odbywa się przy użyciu bezpiecznych funkcji Django (`check_password`).
- **Throttling (Ograniczanie szybkości)**: Zastosowanie `AnonRateThrottle` dla tego endpointu, aby zapobiec atakom Brute Force (np. 5 prób na minutę).
- **Walidacja danych**: Ścisła walidacja typów i formatów w Serializerze.

## 7. Obsługa błędów
- **400 Bad Request**:
  - `missing_field`: "To pole jest wymagane."
  - `invalid_credentials`: "Nieprawidłowy adres e-mail lub hasło." (Komunikat ogólny dla bezpieczeństwa, aby nie zdradzać czy e-mail istnieje).
- **500 Internal Server Error**: Nieoczekiwane błędy po stronie serwera (logowane w standardowym loggerze Django).

## 8. Rozważania dotyczące wydajności
- Zapytanie o użytkownika po polu `email` powinno być szybkie. Warto upewnić się, że pole `email` w modelu User jest indeksowane (w standardowym modelu Django `User` pole `email` nie ma indeksu unique/db_index domyślnie, ale przy tej skali to pomijalne; w przyszłości warto rozważyć indeks).
- Operacja `Token.objects.get_or_create` jest lekka.

## 9. Etapy wdrożenia

### Krok 1: Instalacja i Konfiguracja DRF
Zaktualizuj plik `pyproject.toml` (lub zainstaluj pipem) dodając `djangorestframework`.
Zaktualizuj `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken',
    ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```
*Uruchom migracje (`python manage.py migrate`), aby utworzyć tabele dla tokenów.*

### Krok 2: Tworzenie Serializera
Utwórz plik `pathie/api/serializers.py` i zaimplementuj `LoginSerializer`.
- Użyj `serializers.Serializer`.
- W metodzie `validate` zaimplementuj logikę sprawdzania użytkownika po e-mailu.

### Krok 3: Tworzenie Widoku
Utwórz plik `pathie/api/views.py` i zaimplementuj `LoginAPIView`.
- Wykorzystaj `ObtainAuthToken` jako wzór lub napisz własny `APIView` używający `LoginSerializer`.
- Zapewnij format odpowiedzi `{"key": token.key}`.

### Krok 4: Konfiguracja URL
W pliku `pathie/urls.py` (lub `apps/api/urls.py` jeśli istnieje) dodaj ścieżkę:
```python
path('api/auth/login/', LoginAPIView.as_view(), name='api_login'),
```

### Krok 5: Testowanie
- Uruchom serwer.
- Wykonaj testowe żądanie POST (np. przez curl lub Postman).
- Zweryfikuj poprawność odpowiedzi dla poprawnych i błędnych danych.
