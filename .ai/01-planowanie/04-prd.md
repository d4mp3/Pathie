# Dokument wymagań produktu (PRD) - Pathie (MVP)
## 1. Przegląd produktu
Pathie to aplikacja internetowa (webowa) zaprojektowana, aby rozwiązać problem planowania angażujących i spersonalizowanych wycieczek po mieście. Aplikacja, wykorzystując sztuczną inteligencję, generuje tematyczne trasy zwiedzania wraz z unikalnymi opisami odwiedzanych miejsc, dopasowanymi do indywidualnych zainteresowań użytkownika. Wersja MVP skupia się na dostarczeniu kluczowej wartości, jaką jest tworzenie i zapisywanie tras, z pominięciem zaawansowanych funkcji, takich jak nawigacja w czasie rzeczywistym czy elementy społecznościowe. Celem jest walidacja hipotezy, że użytkownicy potrzebują i będą korzystać z narzędzia, które tworzy spójne narracje wokół miejskich eksploracji.

## 2. Problem użytkownika
Planowanie ciekawych i spójnych tematycznie wycieczek po mieście jest trudne i czasochłonne. Turyści oraz mieszkańcy, którzy chcą odkrywać swoje miasto w nieszablonowy sposób, często napotykają na następujące problemy:
* Standardowe przewodniki oferują te same, utarte szlaki, które nie odpowiadają niszowym lub specyficznym zainteresowaniom.
* Samodzielne łączenie pojedynczych atrakcji w logiczną, interesującą i efektywną czasowo trasę jest skomplikowane.
* Brak jest narzędzi, które nie tylko wskazują miejsca, ale również tworzą wokół nich angażującą opowieść, dopasowaną do perspektywy użytkownika (np. historycznej, artystycznej, kulinarnej).

Pathie adresuje te problemy, automatyzując proces tworzenia spersonalizowanych planów wycieczek i dostarczając unikalne treści, które wzbogacają doświadczenie zwiedzania.

## 3. Wymagania funkcjonalne
### 3.1. System Kont Użytkowników
* Rejestracja użytkownika za pomocą adresu e-mail i hasła.
* Logowanie do systemu za pomocą adresu e-mail i hasła.
* Logowanie i rejestracja.
* Możliwość wylogowania się z aplikacji.
* Dostęp do funkcji generowania i zapisywania tras wymaga bycia zalogowanym.

### 3.2. Generowanie Tras przez AI
* Możliwość wyboru od 1 do 3 predefiniowanych tagów zainteresowań (np. "sztuka", "historia", "kuchnia").
* Opcjonalne pole tekstowe (1000-10000 znaków) do dalszego uszczegółowienia tematu wycieczki.
* Generowanie trasy składającej się z maksymalnie 7 punktów na podstawie wybranych tagów i opisu.
* Generowanie spersonalizowanych opisów dla każdego punktu na trasie, z wykorzystaniem danych z API Wikipedii i OpenStreetMap, dopasowanych do kontekstu zdefiniowanego przez tagi. Opis każdego punktu powinien zawierać od 2500 do 5000 znaków.

### 3.3. Manualne Tworzenie Tras
* Możliwość manualnego wyszukiwania i dodawania punktów na interaktywnej mapie.
* Limit dodawania do 10 punktów w jednej trasie.
* Automatyczna optymalizacja kolejności dodanych punktów w celu stworzenia logicznej trasy zwiedzania.

### 3.4. Interakcja z Trasą
* Wyświetlanie wygenerowanej lub stworzonej trasy w dwóch widokach: lista punktów oraz interaktywna mapa.
* Responsywny interfejs (Mobile-First): domyślny widok listy na urządzeniach mobilnych z opcją przełączenia na mapę; widok dzielony (mapa + lista) na desktopie.
* Możliwość usunięcia pojedynczego punktu z trasy przed jej finalnym zapisaniem.
* Przycisk "Pokaż moją lokalizację" jednorazowo wyświetlający pozycję użytkownika na mapie.
* Przycisk "Nawiguj do" przy każdym punkcie, który otwiera domyślną, zewnętrzną aplikację mapową na urządzeniu użytkownika.
* Możliwość odczytania spersonalizowanych opisów dla każdego punktu na trasie.
* Buforowanie załadowanej trasy (mapa i opisy) w przeglądarce w celu zapewnienia ograniczonej funkcjonalności w trybie offline.

### 3.5. Zarządzanie Trasami
* Wygenerowane trasy mają status tymczasowy do momentu ich zapisu przez użytkownika.
* Możliwość zapisania wygenerowanej lub stworzonej manualnie trasy na koncie użytkownika.
* Automatyczne generowanie nazwy dla zapisanej trasy z możliwością jej późniejszej edycji przez użytkownika.
* Dostęp do listy zapisanych tras.
* Możliwość przeglądania i usuwania zapisanych tras.

### 3.6. System Zbierania Opinii
* Mechanizm oceny (kciuk w górę / kciuk w dół) dla każdego wygenerowanego przez AI opisu miejsca.
* Mechanizm ogólnej oceny (uśmiechnięta / smutna buźka) dla całej wygenerowanej przez AI trasy.

## 4. Granice produktu
### 4.1. Funkcjonalności w zakresie MVP
* System kont użytkowników (rejestracja/logowanie przez e-mail).
* Generowanie tras przez AI na podstawie tagów i opisu tekstowego (do 7 punktów).
* Manualne tworzenie tras z wyszukiwarką miejsc i automatyczną optymalizacją kolejności (do 10 punktów).
* Tworzenie spersonalizowanych opisów miejsc.
* Zapisywanie, przeglądanie i usuwanie własnych tras.
* Podstawowa interakcja z mapą (wyświetlanie trasy, lokalizacji użytkownika na żądanie).
* Integracja z zewnętrznymi aplikacjami nawigacyjnymi.
* System zbierania opinii o trasach i opisach.
* Aplikacja w pełni responsywna (Mobile-First).
* Aplikacja dostępna wyłącznie w języku polskim (interfejs i generowane treści).

### 4.2. Funkcjonalności poza zakresem MVP
* Współdzielenie planów wycieczkowych między użytkownikami.
* Nawigacja GPS "turn-by-turn" w czasie rzeczywistym wewnątrz aplikacji.
* Zaawansowane planowanie czasu i logistyki (np. pory otwarcia, czas przejścia).
* System rekomendacji nowych tras w oparciu o historię i oceny użytkownika.
* Ręczna zmiana kolejności punktów w trasie manualnej.
* Edycja zapisanych tras (np. dodawanie/usuwanie punktów).
* Bogata obsługa multimediów (np. dodawanie zdjęć, wyświetlanie galerii miejsc).
* Dedykowane aplikacje mobilne (iOS, Android).
* Wersje językowe inne niż polska.

## 5. Historyjki użytkowników
### 5.1. Uwierzytelnianie i Zarządzanie Kontem
---
* ID: US-001
* Tytuł: Rejestracja konta za pomocą e-maila
* Opis: Jako nowy użytkownik, chcę móc zarejestrować się w aplikacji przy użyciu mojego adresu e-mail i hasła, aby stworzyć konto i zapisywać moje trasy.
* Kryteria akceptacji:
    1.  Formularz rejestracji zawiera pola: adres e-mail, hasło, powtórz hasło.
    2.  System waliduje poprawność formatu adresu e-mail.
    3.  System wymaga, aby hasła w obu polach były identyczne.
    4.  System waliduje siłę hasła (np. minimum 8 znaków).
    5.  Po pomyślnej rejestracji, użytkownik jest automatycznie zalogowany i przekierowany na stronę główną.
    6.  W przypadku, gdy e-mail jest już zajęty, wyświetlany jest stosowny komunikat.

---
* ID: US-002
* Tytuł: Logowanie na konto za pomocą e-maila
* Opis: Jako zarejestrowany użytkownik, chcę móc zalogować się do aplikacji przy użyciu mojego adresu e-mail i hasła, aby uzyskać dostęp do moich zapisanych tras.
* Kryteria akceptacji:
    1.  Formularz logowania zawiera pola: adres e-mail, hasło.
    2.  Po poprawnym wprowadzeniu danych, użytkownik jest zalogowany i przekierowany na stronę główną.
    3.  W przypadku podania błędnego e-maila lub hasła, wyświetlany jest stosowny komunikat.

---


---
* ID: US-004
* Tytuł: Wylogowanie z aplikacji
* Opis: Jako zalogowany użytkownik, chcę móc się wylogować z aplikacji, aby zabezpieczyć swoje konto na urządzeniu współdzielonym.
* Kryteria akceptacji:
    1.  W interfejsie użytkownika dostępny jest przycisk "Wyloguj".
    2.  Po kliknięciu przycisku, sesja użytkownika jest kończona i jest on przekierowywany na stronę główną (w stanie niezalogowanym).

---
* ID: US-005
* Tytuł: Wymóg logowania do korzystania z głównych funkcji
* Opis: Jako niezalogowany użytkownik, próbując wygenerować trasę, chcę zostać poinformowany o konieczności zalogowania się lub rejestracji, aby zrozumieć, dlaczego funkcja jest niedostępna i móc podjąć dalsze kroki.
* Kryteria akceptacji:
    1.  Główne przyciski akcji (np. "Generuj trasę") są widoczne, ale nieaktywne lub ich kliknięcie powoduje wyświetlenie monitu o zalogowanie/rejestrację.
    2.  Monit zawiera bezpośrednie linki do stron logowania i rejestracji.

### 5.2. Generowanie i Przeglądanie Trasy AI
---
* ID: US-006
* Tytuł: Generowanie trasy przez AI na podstawie zainteresowań
* Opis: Jako zalogowany użytkownik, chcę móc wybrać tagi zainteresowań i opcjonalnie wpisać dodatkowy opis, aby wygenerować spersonalizowaną trasę wycieczki.
* Kryteria akceptacji:
    1.  Na stronie głównej widoczny jest interfejs do generowania trasy.
    2.  Mogę wybrać od 1 do 3 predefiniowanych tagów z listy.
    3.  Widzę opcjonalne pole tekstowe do wpisania opisu o długości od 1000 do 10000 znaków.
    4.  Po kliknięciu przycisku "Generuj", aplikacja wyświetla informację o procesie tworzenia trasy.
    5.  Wynikiem jest wygenerowana, tymczasowa trasa składająca się z maksymalnie 7 punktów.
    6.  System uniemożliwia wygenerowanie trasy z mniej niż 1 lub więcej niż 3 tagami.

---
* ID: US-007
* Tytuł: Przeglądanie wygenerowanej trasy
* Opis: Jako użytkownik, po wygenerowaniu trasy, chcę móc ją przejrzeć na liście i na mapie, aby zdecydować, czy mi odpowiada.
* Kryteria akceptacji:
    1.  Na desktopie widzę jednocześnie listę punktów trasy oraz mapę z zaznaczonymi punktami i linią łączącą je.
    2.  Na mobile'u domyślnie widzę listę punktów z możliwością przełączenia na widok pełnoekranowej mapy.
    3.  Każdy element na liście zawiera nazwę miejsca.
    4.  Kliknięcie na element listy powoduje wycentrowanie mapy na odpowiadającym mu punkcie.

---
* ID: US-008
* Tytuł: Czytanie spersonalizowanych opisów miejsc
* Opis: Jako użytkownik, chcę móc przeczytać unikalne opisy dla każdego miejsca na trasie, aby dowiedzieć się czegoś ciekawego w kontekście moich zainteresowań.
* Kryteria akceptacji:
    1.  Po wybraniu punktu na liście lub mapie, rozwija się sekcja z jego opisem.
    2.  Treść opisu jest dopasowana do tagów oraz dodatkowego tekstu, które wybrałem podczas generowania trasy.
    3.  Opis jest czytelny i sformatowany w przystępny sposób.

---
* ID: US-009
* Tytuł: Usuwanie punktu z tymczasowej trasy
* Opis: Jako użytkownik, chcę mieć możliwość usunięcia punktu z wygenerowanej trasy przed jej zapisaniem, jeśli dany punkt mi nie odpowiada.
* Kryteria akceptacji:
    1.  Przy każdym punkcie na liście widoczny jest przycisk "Usuń".
    2.  Po kliknięciu przycisku, dany punkt znika z listy oraz z mapy.
    3.  Trasa na mapie aktualizuje się, omijając usunięty punkt.

### 5.3. Manualne Tworzenie Trasy
---
* ID: US-010
* Tytuł: Inicjowanie tworzenia trasy manualnej
* Opis: Jako zalogowany użytkownik, chcę mieć możliwość przełączenia się do trybu manualnego tworzenia trasy, aby samodzielnie wybrać miejsca, które chcę odwiedzić.
* Kryteria akceptacji:
    1.  Na stronie głównej znajduje się wyraźna opcja wyboru trybu manualnego.
    2.  Po jej wybraniu, interfejs zmienia się, pokazując mapę z polem wyszukiwania.

---
* ID: US-011
* Tytuł: Dodawanie punktów do trasy manualnej
* Opis: Jako użytkownik w trybie manualnym, chcę móc wyszukiwać miejsca i dodawać je do mojej trasy, aby stworzyć własny plan wycieczki.
* Kryteria akceptacji:
    1.  Mogę wpisać nazwę lub adres w polu wyszukiwania.
    2.  System wyświetla pasujące wyniki.
    3.  Mogę wybrać punkt z wyników lub bezpośrednio z mapy, aby dodać go do trasy.
    4.  Dodane punkty pojawiają się na liście i na mapie.
    5.  Nie mogę dodać więcej niż 10 punktów. Po dodaniu 10. punktu opcja dodawania kolejnych jest blokowana.

---
* ID: US-012
* Tytuł: Automatyczna optymalizacja kolejności trasy manualnej
* Opis: Jako użytkownik, po dodaniu wszystkich punktów w trybie manualnym, chcę, aby aplikacja automatycznie ułożyła je w optymalnej kolejności zwiedzania, abym nie musiał robić tego samodzielnie.
* Kryteria akceptacji:
    1.  Po zakończeniu dodawania punktów (np. po kliknięciu przycisku "Zakończ i zoptymalizuj"), ich kolejność na liście i na mapie zostaje przearanżowana.
    2.  Nowa kolejność tworzy najkrótszą lub najbardziej logiczną ścieżkę łączącą wszystkie punkty.

### 5.4. Interakcja z Mapą i Nawigacja
---
* ID: US-013
* Tytuł: Lokalizowanie siebie na mapie
* Opis: Jako użytkownik korzystający z aplikacji w terenie, chcę móc szybko zlokalizować swoją aktualną pozycję na mapie trasy, aby zorientować się, gdzie jestem.
* Kryteria akceptacji:
    1.  Na widoku mapy znajduje się przycisk "Pokaż moją lokalizację".
    2.  Po kliknięciu przycisku, przeglądarka prosi o zgodę na udostępnienie lokalizacji (jeśli to pierwsze użycie).
    3.  Po wyrażeniu zgody, na mapie pojawia się znacznik wskazujący moją aktualną pozycję.

---
* ID: US-014
* Tytuł: Rozpoczynanie nawigacji do punktu
* Opis: Jako użytkownik, będąc przy jednym punkcie trasy, chcę łatwo uruchomić nawigację do następnego punktu, korzystając z mojej ulubionej aplikacji mapowej.
* Kryteria akceptacji:
    1.  Każdy punkt na trasie ma przycisk "Nawiguj do".
    2.  Kliknięcie przycisku otwiera domyślną aplikację mapową (np. Google Maps, Apple Maps) na moim urządzeniu z już wyznaczoną trasą do danego punktu.

### 5.5. Zarządzanie Zapisanymi Trasami
---
* ID: US-015
* Tytuł: Zapisywanie tymczasowej trasy
* Opis: Jako użytkownik, po wygenerowaniu lub stworzeniu trasy, która mi się podoba, chcę móc ją zapisać na moim koncie, aby mieć do niej dostęp w przyszłości.
* Kryteria akceptacji:
    1.  W widoku trasy tymczasowej znajduje się przycisk "Zapisz wycieczkę".
    2.  Po kliknięciu, trasa jest zapisywana, a system nadaje jej automatycznie wygenerowaną nazwę (np. na podstawie tagów lub lokalizacji).
    3.  Użytkownik otrzymuje potwierdzenie, że trasa została zapisana.

---
* ID: US-016
* Tytuł: Przeglądanie listy zapisanych tras
* Opis: Jako zalogowany użytkownik, chcę mieć dostęp do listy wszystkich moich zapisanych tras, aby móc do nich wrócić.
* Kryteria akceptacji:
    1.  W interfejsie aplikacji znajduje się sekcja "Moje trasy".
    2.  W tej sekcji widzę listę wszystkich tras, które zapisałem.
    3.  Każdy element listy wyświetla nazwę trasy i być może kluczowe informacje (np. liczba punktów).
    4.  Kliknięcie na trasę z listy otwiera jej szczegółowy widok.

---
* ID: US-017
* Tytuł: Zmiana nazwy zapisanej trasy
* Opis: Jako użytkownik, chcę mieć możliwość zmiany automatycznie nadanej nazwy zapisanej trasy, aby nadać jej własną, łatwiejszą do zapamiętania nazwę.
* Kryteria akceptacji:
    1.  W widoku zapisanej trasy znajduje się opcja edycji jej nazwy.
    2.  Po wprowadzeniu nowej nazwy i jej zatwierdzeniu, nazwa jest aktualizowana na liście tras i w jej widoku szczegółowym.

---
* ID: US-018
* Tytuł: Usuwanie zapisanej trasy
* Opis: Jako użytkownik, chcę móc usunąć zapisaną trasę, której już nie potrzebuję, aby utrzymać porządek na mojej liście.
* Kryteria akceptacji:
    1.  Na liście tras lub w widoku szczegółowym trasy znajduje się przycisk "Usuń".
    2.  Przed ostatecznym usunięciem aplikacja prosi o potwierdzenie tej operacji.
    3.  Po potwierdzeniu, trasa jest trwale usuwana z konta użytkownika.

### 5.6. System Opinii
---
* ID: US-019
* Tytuł: Ocenianie jakości opisu miejsca
* Opis: Jako użytkownik, po przeczytaniu opisu danego miejsca, chcę móc go ocenić, aby dać twórcom aplikacji znać, czy treść była dla mnie interesująca.
* Kryteria akceptacji:
    1.  Przy każdym opisie miejsca wygenerowanym przez AI widoczne są ikony "kciuk w górę" i "kciuk w dół".
    2.  Mogę kliknąć jedną z ikon, aby zarejestrować swoją opinię.
    3.  Po kliknięciu, ikona zmienia wygląd, sygnalizując, że głos został oddany. Możliwa jest zmiana głosu.

---
* ID: US-020
* Tytuł: Ocenianie całej wygenerowanej trasy
* Opis: Jako użytkownik, po przejrzeniu całej wygenerowanej przez AI trasy, chcę móc ją ogólnie ocenić, aby przekazać informację zwrotną na temat jakości propozycji.
* Kryteria akceptacji:
    1.  W widoku wygenerowanej trasy znajdują się ikony (np. uśmiechnięta i smutna buźka) do jej oceny.
    2.  Mogę kliknąć jedną z ikon, aby ocenić całą trasę.
    3.  System zapisuje moją ocenę.

### 5.7. Dostępność
---
* ID: US-021
* Tytuł: Dostęp do załadowanej trasy w trybie offline
* Opis: Jako użytkownik, który jest w trakcie zwiedzania i może stracić połączenie z internetem, chcę nadal mieć dostęp do raz załadowanej trasy i opisów, aby móc kontynuować wycieczkę.
* Kryteria akceptacji:
    1.  Po pierwszym załadowaniu widoku trasy, jej dane (punkty, opisy, fragment mapy) są buforowane w przeglądarce.
    2.  W przypadku utraty połączenia z internetem, nadal mogę przeglądać listę punktów, czytać ich opisy i widzieć ich rozmieszczenie na mapie.
    3.  Funkcje wymagające połączenia (np. "Nawiguj do", ładowanie nowych fragmentów mapy, "Pokaż moją lokalizację") są niedostępne i odpowiednio oznaczone.

## 6. Metryki sukcesu
Kluczowe metryki, które pozwolą na ocenę sukcesu wersji MVP produktu:

* Kryterium 1: Akceptacja Tras
    * Cel: 70% wygenerowanych przez AI tras jest akceptowanych przez użytkownika.
    * Sposób pomiaru: Mierzone jako procent wygenerowanych tras, dla których użytkownik wykonał co najmniej jedną z dwóch akcji:
        1.  Kliknął przycisk "Zapisz wycieczkę".
        2.  Kliknął przycisk "Nawiguj do" przy dowolnym punkcie na trasie.
    * Uzasadnienie: Obie akcje wskazują na silną intencję skorzystania z zaproponowanej trasy, co jest wskaźnikiem jej trafności i użyteczności.

* Kryterium 2: Jakość Treści
    * Cel: 70% wygenerowanych opisów miejsc na trasie jest ocenianych jako trafne i interesujące.
    * Sposób pomiaru: Mierzony jako stosunek liczby ocen "kciuk w górę" do łącznej liczby ocen (kciuk w górę + kciuk w dół) dla wszystkich wygenerowanych opisów.
    * Uzasadnienie: Ta metryka bezpośrednio mierzy jakość kluczowego elementu produktu - spersonalizowanych treści, które mają wzbogacać doświadczenie zwiedzania.