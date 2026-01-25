# Architektura UI dla Pathie

## 1. Przegląd struktury UI

Interfejs użytkownika Pathie został zaprojektowany zgodnie z paradygmatem **Mobile-First**, kładąc nacisk na czytelność, szybkość działania i płynność interakcji w warunkach podróży. Architektura opiera się na **Server-Driven UI** (Django Templates + HTMX), co pozwala na dynamiczną wymianę fragmentów widoku bez pełnego przeładowania strony, zachowując jednocześnie prostotę backendu.

Kluczowe filary architektury:
*   **Minimalizm:** Skupienie na treści (opisach miejsc i mapie). Rezygnacja z Dark Mode na rzecz czytelnego, wysokokontrastowego trybu jasnego (Light Mode).
*   **Płynność (App-like feel):** Wykorzystanie View Transitions API oraz animacji CSS do maskowania ładowania danych (Skeleton Screens).
*   **Odporność:** Strategia Offline-First dla załadowanych tras (Service Worker) oraz obsługa błędów sieciowych.
*   **Hybrydowy stan:** Stan aplikacji synchronizowany przez HTMX (serwer) oraz Alpine.js (interakcje lokalne, modale, mapy).

## 2. Lista widoków

### 2.1. Strona Powitalna (Landing Page)
*   **Ścieżka:** `/`
*   **Główny cel:** Konwersja odwiedzającego w zarejestrowanego użytkownika. Edukacja o wartości produktu.
*   **Kluczowe informacje:** Value Proposition, Call to Action (Zaloguj/Zarejestruj), przykładowe trasy (statyczne).
*   **Kluczowe komponenty:** `HeroSection`, `FeatureList`, `AuthButtons`.
*   **UX/A11y/Security:** Wysoki kontrast CTA. Dostępna nawigacja klawiaturą.

### 2.2. Logowanie / Rejestracja
*   **Ścieżka:** `/auth/login/`, `/auth/details/`
*   **Główny cel:** Uwierzytelnienie użytkownika.
*   **Kluczowe informacje:** Formularze email/hasło, komunikaty błędów walidacji.
*   **Kluczowe komponenty:** `AuthForm`, `SocialLogin` (przyszłościowo), `ErrorToast`.
*   **UX/A11y/Security:** Walidacja inline. Obsługa menedżerów haseł. Ochrona CSRF.

### 2.3. Dashboard (Moje Trasy)
*   **Ścieżka:** `/dashboard/`
*   **Główny cel:** Centralny punkt dostępu do zapisanych tras i start nowych.
*   **Kluczowe informacje:** Lista zapisanych tras (nazwa, data, liczba punktów), stan pusty (jeśli brak tras).
*   **Kluczowe komponenty:** `RouteCard`, `EmptyStateIllustration`, `FloatingActionButton` (CTA: Nowa trasa).
*   **UX/A11y/Security:** Twarde przekierowanie (HX-Redirect) przy wygaśnięciu sesji. Łatwe usuwanie tras.

### 2.4. Kreator Trasy (Wybór Trybu)
*   **Ścieżka:** `/routes/new/`
*   **Główny cel:** Decyzja użytkownika o sposobie planowania (AI vs Manual).
*   **Kluczowe informacje:** Dwie karty wyboru z opisem zalet.
*   **Kluczowe komponenty:** `ModeSelectionCard`.

### 2.5. Kreator AI (Formularz)
*   **Ścieżka:** `/routes/new/ai/`
*   **Główny cel:** Zebranie preferencji do generowania.
*   **Kluczowe informacje:** Lista dostępnych tagów, pole na opis.
*   **Kluczowe komponenty:** `TagSelector` (pigułki), `ConstraintTextArea` (licznik znaków), `SubmitButton` (z loaderem).
*   **UX/A11y/Security:** Blokada przycisku przed wybraniem tagów.

### 2.6. Ekran Generowania (Intermedialny)
*   **Ścieżka:** `/routes/generating/`
*   **Główny cel:** Utrzymanie uwagi użytkownika podczas oczekiwania na LLM.
*   **Kluczowe informacje:** Pasek postępu, ciekawostki o mieście (zmienne teksty).
*   **Kluczowe komponenty:** `SkeletonLoader`, `TriviaWidget`.
*   **UX/A11y/Security:** Ukrycie opóźnień API.

### 2.7. Kreator Manualny
*   **Ścieżka:** `/routes/new/manual/`
*   **Główny cel:** Ręczne dodawanie punktów.
*   **Kluczowe informacje:** Mapa, wyszukiwarka miejsc, lista dodanych punktów.
*   **Kluczowe komponenty:** `MapSearchBox`, `DraggablePointList`, `OptimizeButton`.

### 2.8. Widok Trasy (Szczegóły)
*   **Ścieżka:** `/routes/{id}/`
*   **Główny cel:** Konsumpcja treści, nawigacja w terenie.
*   **Kluczowe informacje:** Mapa trasy, lista punktów, opisy, oceny.
*   **Kluczowe komponenty:** 
    *   **Mobile:** `ViewToggleFAB` (Mapa/Lista), `PointListItem`.
    *   **Desktop:** `SplitLayout` (Lista lewo, Mapa prawo).
    *   `StickySaveBar` (dla tras tymczasowych).
    *   `InlineTitleEdit`.
*   **UX/A11y/Security:** Dwukierunkowa synchronizacja scrolla z mapą. Service Worker cache'ujący ten widok. Guard (modal) przy próbie wyjścia bez zapisu.

### 2.9. Szczegóły Punktu (Drill-down)
*   **Ścieżka:** `/routes/{id}/points/{point_id}/` (lub modal query param)
*   **Główny cel:** Głębokie zapoznanie się z opisem miejsca.
*   **Kluczowe informacje:** Pełny opis AI, zdjęcie, adres, przycisk nawigacji.
*   **Kluczowe komponenty:** `DetailView`, `RatingWidget` (Optimistic UI), `ExternalNavButton`.

## 3. Mapa podróży użytkownika

### Scenariusz Główny: Szybka wycieczka z AI

1.  **Start:** Użytkownik wchodzi na stronę główną -> Klika "Rozpocznij".
2.  **Auth:** Loguje się danymi zapisanymi w przeglądarce.
3.  **Dashboard:** Widzi puste "Moje trasy". Klika FAB "+".
4.  **Wybór:** Wybiera "Generator AI".
5.  **Preferencje:** Zaznacza "Architektura" i "Kawa". Wpisuje "Spacer bez pośpiechu". Klika "Generuj".
6.  **Oczekiwanie:** Widzi animowany szkielet i czyta ciekawostkę ("Czy wiesz, że...").
7.  **Wynik (Widok Trasy):** Otrzymuje trasę.
    *   *Mobile:* Przegląda listę punktów. Przełącza FAB-em na mapę, by zobaczyć rozkład.
    *   *Desktop:* Widzi mapę i listę obok siebie.
8.  **Weryfikacja:** Klika w pierwszy punkt, czyta opis. Daje "Łapkę w górę" (Optimistic UI - ikona zmienia się natychmiast).
9.  **Zapis:** Pasek na dole sugeruje "Trasa tymczasowa". Klika "Zapisz".
10. **Edycja:** Klika w ikonę ołówka przy tytule, zmienia nazwę na "Niedzielny spacer".
11. **Koniec:** Wraca do Dashboardu, widzi nową trasę na liście.

## 4. Układ i struktura nawigacji

### Globalny Układ (Layout)
*   **Header:**
    *   Logo (lewa).
    *   Menu użytkownika / Avatar (prawa).
    *   Wskaźnik statusu offline (ukryty domyślnie).
*   **Main:** Kontener na treść (zmienia się via HTMX).
*   **Footer:** (Tylko informacyjny, copyright - minimalistyczny).

### Nawigacja Wewnątrz Widoku Trasy
Zastosowano dualny model nawigacji zależny od urządzenia (RWD):

1.  **Mobile (Stack View):**
    *   Domyślnie: Lista punktów.
    *   Pływający przycisk (FAB) w prawym dolnym rogu: Ikona Mapy.
    *   Akcja FAB: Przełącza widok na pełnoekranową mapę (zachowując stan, bez przeładowania).
    *   FAB na mapie: Ikona Listy (powrót).
    *   Kliknięcie w punkt na liście: Przejście (animowane, view transition) do szczegółów punktu.

2.  **Desktop (Split View):**
    *   Stały podział ekranu: 40% szerokości Lista (lewa, scrollowana), 60% Mapa (prawa, fixed).
    *   Interakcja: Kliknięcie punktu na mapie scrolluje listę do odpowiedniej pozycji. Kliknięcie na liście centruje mapę.

## 5. Kluczowe komponenty

1.  **Sticky Save Bar (Guard)**
    *   Pasek przyklejony do krawędzi ekranu (dół na mobile, góra/dół na desktop), widoczny tylko dla tras o statusie `temporary`. Zawiera przycisk "Zapisz" i "Modyfikuj". Chroni przed przypadkowym wyjściem.

2.  **Rating Widget (Optimistic)**
    *   Komponent Alpine.js. Po kliknięciu natychmiast zmienia stan wizualny (active), wysyła żądanie w tle. W razie błędu cofa zmianę i wyświetla Toast.

3.  **Skeleton Screen Loader**
    *   Zestaw szarych, pulsujących bloków imitujących układ docelowej treści (zdjęcie + tekst), używany podczas ładowania trasy z API, aby zmniejszyć postrzegany czas oczekiwania.

4.  **Toast Notification System**
    *   Kontener powiadomień obsługiwany przez zdarzenia `htmx:afterRequest`. Wyświetla błędy walidacji lub potwierdzenia akcji ("Zapisano").

5.  **Service Worker Cache**
    *   Skrypt działający w tle, przechwytujący żądania do `/api/routes/{id}/`. Zapisuje plik HTML odpowiedzi, umożliwiając odtworzenie widoku trasy bez zasięgu.

6.  **Inline Edit Field**
    *   Nagłówek trasy, który po kliknięciu ikony ołówka zamienia się w `input`. Zapisuje zmianę po utracie focusu (`hx-trigger="blur"`).
