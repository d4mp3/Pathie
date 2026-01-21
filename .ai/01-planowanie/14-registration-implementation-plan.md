# API Endpoint Implementation Plan: Rejestracja Użytkownika

## 1. Przegląd punktu końcowego
Punkt końcowy `POST /api/auth/registration/` służy do rejestracji nowych użytkowników w systemie. Umożliwia utworzenie konta przy użyciu adresu e-mail i hasła, zwracając w odpowiedzi token uwierzytelniający, który pozwala na natychmiastowe korzystanie z chronionych zasobów API.

## 2. Szczegóły żądania
- **Metoda HTTP**: `POST`
- **Struktura URL**: `/api/auth/registration/`
- **Parametry**: Brak (parametry URL).
- **Request Body** (`application/json`):
  - **Wymagane pola**:
    - `email`: (string) Unikalny adres e-mail użytkownika.
    - `password`: (string) Hasło użytkownika.
    - `password_confirm`: (string) Potwierdzenie hasła.

  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
  }
  ```

## 3. Wymagane komponenty (Modele, Serializery, Widoki)

### Modele
- **`django.contrib.auth.models.User`**: Wykorzystamy standardowy model użytkownika Django.
  - *Uwaga*: Ponieważ rejestracja opiera się na `email`, pole `username` modelu User zostanie automatycznie wypełnione wartością `email` (lub skrótem, jeśli email jest długi, ale w tym przypadku przyjmujemy `username = email`).
- **`rest_framework.authtoken.models.Token`**: Do generowania i przechowywania tokenów autoryzacyjnych.

### Serializery
- **`RegistrationSerializer`** (nowy):
  - Walidacja zgodności haseł (`password` vs `password_confirm`).
  - Walidacja unikalności adresu e-mail.
  - Walidacja siły hasła (opcjonalnie, przy użyciu waliatorów Django).
- **`UserSerializer`** (istniejący lub nowy): Do sformatowania danych użytkownika w odpowiedzi.

### Widoki
- **`RegistrationView`**: Widok oparty na `GenericAPIView` lub `APIView` z metodą `post`.
  - Powinien być publicznie dostępny (`AllowAny`).

## 4. Szczegóły odpowiedzi

### Sukces (`201 Created`)
W przypadku pomyślnej rejestracji zwracany jest token oraz podstawowe dane użytkownika.

```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "email": "user@example.com"
}
```

### Błędy
- **`400 Bad Request`**: Błędy walidacji.
  - Nieprawidłowy format email.
  - Hasła się nie zgadzają.
  - Email jest już zajęty.
  - Hasło jest zbyt słabe.

Przykład błędu:
```json
{
  "email": ["Użytkownik z tym adresem email już istnieje."],
  "password_confirm": ["Hasła nie są identyczne."]
}
```

## 5. Przepływ danych
1. **Klient** wysyła żądanie `POST` z JSON-em (email, hasło).
2. **Django URL Dispatcher** kieruje żądanie do `RegistrationView`.
3. **RegistrationView** przekazuje dane do `RegistrationSerializer`.
4. **RegistrationSerializer**:
   - Sprawdza poprawność formatu danych.
   - Sprawdza, czy `password` == `password_confirm`.
   - Sprawdza, czy `email` nie istnieje w bazie (`User.objects.filter(email=...)`).
5. **Logika zapisu (Serializer.save() / View)**:
   - Tworzony jest obiekt `User` (metoda `create_user`).
   - `username` jest ustawiane na wartość `email`.
   - Hasło jest haszowane.
6. **Generowanie tokena**:
   - Tworzony jest lub pobierany `Token` dla nowego użytkownika.
7. **Odpowiedź**:
   - Widok zwraca kod `201` i dane JSON z tokenem.

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie**: Endpoint musi być dostępny bez logowania (Permission: `AllowAny`).
- **Walidacja haseł**: Wykorzystanie `django.contrib.auth.password_validation` do sprawdzenia siły hasła przed utworzeniem użytkownika.
- **Sanityzacja**: Django ORM chroni przed SQL Injection. DRF Serializers chronią przed XSS w odpowiedziach (choć tu zwracamy JSON).
- **HTTPS**: Wdrożenie produkcyjne musi wymuszać HTTPS, aby chronić przesyłane hasła.

## 7. Obsługa błędów
- Wykorzystanie wyjątków `ValidationError` z Django REST Framework.
- Standardowa struktura błędów DRF (klucz pola -> lista błędów).
- Logowanie krytycznych błędów serwera (500) przez standardowy logger Django (`logging.getLogger('django')`).

## 8. Rozważania dotyczące wydajności
- **Indeksy**: Pola `username` i `email` w modelu User są indeksowane, więc sprawdzanie unikalności będzie szybkie.
- **Transakcje**: Operacja utworzenia użytkownika i tokena powinna być atomowa (dekorator `@transaction.atomic`), aby nie pozostawić "osieroconych" użytkowników bez tokena w razie błędu.

## 9. Etapy wdrożenia

### Krok 1: Konfiguracja Django REST Framework
Upewnij się, że `rest_framework` i `rest_framework.authtoken` są w `INSTALLED_APPS` w `pathie/settings.py`.
Uruchom migracje: `python manage.py migrate` (aby utworzyć tabelę tokenów).

### Krok 2: Implementacja Serializera
Utwórz klasę `RegistrationSerializer` w `pathie/core/serializers.py`.
- Zaimplementuj metodę `validate` do sprawdzania haseł.
- Zaimplementuj metodę `create` do tworzenia użytkownika.

### Krok 3: Implementacja Widoku
Utwórz klasę `RegistrationView` w `pathie/core/views.py`.
- Ustaw `permission_classes = [AllowAny]`.
- Obsłuż metodę `post`.

### Krok 4: Konfiguracja URL
Dodaj ścieżkę do `pathie/pathie/urls.py` (lub `pathie/core/urls.py` i zainclude'uj).
- Np. `path('api/auth/registration/', RegistrationView.as_view(), name='auth_register')`.

### Krok 5: Manualne Testy / Weryfikacja
- Wyślij żądanie POST przez Postman/cURL.
- Sprawdź, czy użytkownik powstał w bazie.
- Sprawdź, czy token został zwrócony.
- Sprawdź obsługę błędu przyduplikacie emaila.
