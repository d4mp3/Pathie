# Plan implementacji widoku Strony Powitalnej (Landing Page)

## 1. Przegląd
Strona powitalna (`Landing Page`) pełni podwójną rolę w aplikacji Pathie. Dla niezalogowanych użytkowników (Gości) jest to strona marketingowa z propozycją wartości (Value Proposition) i zachętą do rejestracji, umożliwiająca podgląd interfejsu generatora tras. Dla zalogowanych użytkowników (Użytkowników) staje się głównym pulpitem (Dashboardem) służącym do generowania nowych tras (AI/Manual) oraz zarządzania nimi. Widok musi być responsywny (Mobile-First), estetyczny i dynamiczny, wykorzystując stos technologiczny: Django Templates + Alpine.js + Tailwind CSS.

## 2. Routing widoku
*   **URL:** `/` (Root)
*   **Nazwa widoku Django:** `landing_page`
*   **Dostęp:** Publiczny (z różnymi stanami dla Gościa i Użytkownika)

## 3. Struktura komponentów
Hierarchia komponentów w szablonie (logiczna struktura `block content`):

*   `MainLayout` (`base.html`)
    *   `NavBar` (Globalny - zarządza logowaniem/wylogowaniem)
    *   `LandingContainer` (Główny kontener strony)
        *   `HeroSection` (Nagłówek, Value Prop - widoczny głównie dla Gości)
        *   `RouteWizardModule` (Główny moduł funkcjonalny - Alpine.js Component)
            *   `WizardModeSwitcher` (Przełącznik AI / Manual)
            *   `AIGeneratorForm` (Formularz: Tagi, Opis)
                *   `TagSelector` (Pigułki z tagami)
            *   `ManualPlannerForm` (Formularz: Wyszukiwarka, Mapa - uproszczona)
            *   `AuthPromptModal` (Modal wymuszający logowanie dla akcji chronionych)
        *   `RouteResultModule` (Widoczny po wygenerowaniu trasy - Alpine.js Component)
            *   `ViewModeToggle` (Tylko Mobile: Lista <-> Mapa)
            *   `RoutePointsList` (Lista punktów z detalami)
                *   `PointCard` (Pojedynczy punkt: Nazwa, Opis, Akcje)
            *   `InteractiveMap` (Komponent mapy Leaflet)
            *   `RouteActionBar` (Zapisz, Odrzuć, Oceń)
    *   `Footer`

## 4. Szczegóły komponentów

### `LandingContainer` (Widok Django)
*   **Opis:** Główny wrapper renderowany przez Django. Przekazuje wstępne dane (np. listę tagów, status autoryzacji) do komponentów Alpine.js poprzez `x-data`.
*   **Główne elementy:** `div` z atrybutami `x-data`.
*   **Interakcje:** Inicjalizacja stanu aplikacji.
*   **Propsy (Context Django):**
    *   `user_is_authenticated`: boolean
    *   `available_tags`: List[TagDTO]

### `RouteWizardModule` (Komponent Alpine.js: `x-data="routeWizard()"`)
*   **Opis:** Zarządza stanem tworzenia trasy. Obsługuje logikę formularza, walidację i komunikację z API (generowanie).
*   **Główne elementy:** Formularze HTML, inputy, przyciski sterujące stanem `mode`.
*   **Stan (Alpine):**
    *   `mode`: `'ai' | 'manual'`
    *   `selectedTags`: `number[]` (IDs)
    *   `description`: `string`
    *   `isGenerating`: `boolean`
    *   `generatedRoute`: `RouteDTO | null`
*   **Wymagana walidacja:**
    *   AI Mode: Min 1 tag, Max 3 tagi. Opis < 10000 znaków.
    *   Manual Mode: Max 10 punktów.
*   **Interakcje:**
    *   Zmiana trybu (AI/Manual).
    *   Wybór tagów (toggle).
    *   Submit -> Call API `POST /api/routes/`.
    *   Jeśli `!user_is_authenticated` przy próbie Submit -> Otwórz `AuthPromptModal`.

### `RouteResultModule` (Komponent Alpine.js: wewnątrz `routeWizard` lub osobny `x-data`)
*   **Opis:** Wyświetla wynik działania kreatora. Zarządza widokiem mapy i listy.
*   **Główne elementy:** Kontener `flex` (desktop) lub `block` (mobile), lista `ul`, kontener mapy `div id="map"`.
*   **Stan (Alpine):**
    *   `activeView`: `'list' | 'map'` (Mobile only)
    *   `expandedPointId`: `number | null` (Dla opisów)
    *   `mapInstance`: `LeafletObject`
*   **Interakcje:**
    *   Przełączanie widoku (Mobile): Zmienia widoczność kontenerów.
    *   Kliknięcie punktu na liście: Centrowanie mapy + Rozwinięcie opisu.
    *   Kliknięcie markera na mapie: Scroll do elementu listy + Rozwinięcie.
    *   Usunięcie punktu: Aktualizacja stanu lokalnego (usunięcie z arraya i mapy).
    *   Zapisanie trasy: Call API `PATCH /api/routes/{id}/` (zmiana statusu na `saved`).

### `AuthPromptModal`
*   **Opis:** Prosty modal informujący o konieczności logowania.
*   **Główne elementy:** Overlay, Dialog, Przyciski akcji (linki).
*   **Interakcje:** Zamknięcie modala, Przejście do logowania.

## 5. Typy

### `TagDTO`
*   **Pola:**
    *   `id`: Integer (ID tagu z bazy)
    *   `name`: String (Wyświetlana nazwa, np. "Historia")
    *   `description`: String (Tooltip/Opis)

### `RoutePointDTO`
*   **Pola:**
    *   `id`: Integer (ID punktu)
    *   `order`: Integer (Kolejność w trasie 1..N)
    *   `place`: Obiekt
        *   `name`: String (Nazwa miejsca)
        *   `lat`: Float (Szerokość geograficzna)
        *   `lon`: Float (Długość geograficzna)
        *   `address`: String (Adres opcjonalny)
    *   `description`: Obiekt
        *   `content`: String (Treść opisu, może być HTML)

### `RouteDTO`
*   **Pola:**
    *   `id`: Integer (Opcjonalne ID trasy, jeśli zapisana tymczasowo w DB)
    *   `status`: String ('temporary', 'saved')
    *   `route_type`: String ('ai_generated', 'manual')
    *   `points`: Lista[RoutePointDTO] (Punkty trasy)

## 6. Zarządzanie stanem
Zarządzanie stanem odbywa się po stronie klienta przy użyciu **Alpine.js**.
*   Wymagany customowy store lub funkcja `data()` (np. `routeWizard()`), która trzyma cały stan kreatora i wynikowej trasy.
*   Stan jest "efemeryczny" (trwa do odświeżenia strony), chyba że zastosujemy `Alpine.persist` (opcjonalnie dla User Experience).
*   Dla mapy Leaflet, Alpine.js będzie działać jako wrapper (`x-init`), inicjalizując mapę i nasłuchując zmian w tablicy `points`.

## 7. Integracja API
Komunikacja z backendem odbywa się asynchronicznie (AJAX/Fetch).

*   **Generowanie Trasy (AI):**
    *   **Metoda:** `POST`
    *   **URL:** `/api/routes/`
    *   **Request Body:** `{"route_type": "ai_generated", "tags": [1, 3], "description": "..."}`
    *   **Response:** Obiekt `RouteDTO`

*   **Zapisywanie Trasy:**
    *   **Metoda:** `PATCH`
    *   **URL:** `/api/routes/{id}/`
    *   **Request Body:** `{"status": "saved", "name": "Moja wycieczka"}`
    *   **Response:** `200 OK`

*   **Pobieranie Tagów:**
    *   Pobierane przy renderowaniu serwerowym (Django Context) i przekazywane do Alpine.js jako JSON (`{{ available_tags|json_script:"tags-data" }}`).

## 8. Interakcje użytkownika
1.  **Wybór tagów:** Użytkownik klika w pigułki tagów. Alpine dodaje/usuwa ID z tablicy `selectedTags`.
2.  **Generowanie:** Kliknięcie "Generuj" blokuje przycisk (`loading=true`), wysyła request. Po sukcesie ukrywa formularz, pokazuje widok trasy.
3.  **Mapa/Lista (Mobile):** Użytkownik klika "Mapa" -> lista znika (`display: none`), mapa się pokazuje (`height: 100%`).
4.  **Interakcja z Mapą:** Kliknięcie w marker wywołuje event w Alpine, który znajduje odpowiedni element listy i rozwija go (`expandedPointId = id`).

## 9. Warunki i walidacja
Walidacja odbywa się dwuetapowo:

1.  **Interfejs (Alpine.js):**
    *   Przycisk "Generuj" jest `disabled` jeśli: `selectedTags.length < 1` lub `selectedTags.length > 3`.
    *   Licznik znaków pola opis pokazuje się na czerwono po przekroczeniu 10000 znaków.
2.  **API (Django REST Framework):**
    *   Zwraca błędy `400 Bad Request` w formacie JSON, które muszą być sparsowane przez frontend i wyświetlone użytkownikowi (np. "Wybrano nieprawidłowe tagi").

## 10. Obsługa błędów
*   **Błędy API:** Blok `try...catch` w funkcjach asynchronicznych Alpine. Błąd jest zapisywany w zmiennej `error` i wyświetlany jako alert nad formularzem.
*   **Błędy Mapy:** Jeśli mapa nie może się załadować (brak sieci dla kafelków), Leaflet wyświetli puste tło, ale punkty powinny nadal być iterowalne na liście.
*   **Sesja wygasła:** Jeśli API zwróci `401 Unauthorized`, frontend automatycznie przekierowuje do `/login` lub otwiera modal.

## 11. Kroki implementacji
1.  **Backend:** Upewnić się, że `views.py` dla ścieżki `/` zwraca `available_tags` w kontekście.
2.  **Szablon:** Utworzyć plik `landing.html` rozszerzający `base.html`.
3.  **Alpine Component:** Stworzyć plik JS (lub w bloku `script`) z logiką `routeWizard()`.
4.  **UI - Formularz:** Ostylować sekcję Hero i grid tagów w Tailwind.
5.  **Mapa:** Zaimplementować kontener mapy i inicjalizację Leaflet wewnątrz Alpine `x-init`.
6.  **Logika API:** Dodać metody `fetch` do obsługi endpointów `/api/routes/`.
7.  **Szczegóły UI:** Dodać logikę pokazywania/ukrywania opisów (akordeon) i responsywność widoku (ukrywanie mapy na mobile).
8.  **Weryfikacja:** Przetestować przepływ dla użytkownika zalogowanego i niezalogowanego.
