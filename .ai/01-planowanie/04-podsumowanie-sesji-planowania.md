\<conversation\_summary\>
\<decisions\>

1.  **Główna funkcjonalność:** Podstawą aplikacji jest generowanie tras przez AI na podstawie predefiniowanych tagów (np. "sztuka", "historia", "kuchnia", "społeczeństwo") oraz dodatkowym polu tekstowym (od 1000 do 10000 znaków). Funkcja manualnego tworzenia trasy jest opcją drugorzędną.
2.  **Personalizacja treści:** AI będzie generować opisy miejsc, posiłkując się dodatkowo API Wikipedii jako źródło wiedzy. Treść opisu będzie dopasowana do wybranych przez użytkownika tagów (np. dla tagu "historia" AI skupi się na faktach historycznych dotyczących danego miejsca).
3.  **Konto użytkownika:** Rejestracja będzie możliwa przez e-mail/hasło oraz logowanie Google. Zbierane będą tylko minimalne, niezbędne dane.
4.  **Technologia i koszty:** Dane o lokalizacjach będą pobierane z OpenStreetMap. Do generowania treści używany będzie OpenRouter, z zaimplementowanym limitem zapytań w kluczu API w celu monitorowania i kontroli kosztów.
5.  **Interfejs użytkownika (UI):** Aplikacja webowa będzie w pełni responsywna (Mobile-First). Widok na desktopie będzie dzielony (mapa + lista), a na mobile'u domyślna będzie lista z opcją przełączenia na mapę.
6.  **Nawigacja:** Aplikacja nie będzie posiadać wbudowanej nawigacji "turn-by-turn". Zamiast tego, będzie wyświetlać mapę z punktami oraz jednorazowo pokazywać pozycję użytkownika po kliknięciu przycisku. Każdy punkt na trasie będzie miał przycisk "Nawiguj do", otwierający zewnętrzną, domyślną aplikację mapową.
7.  **Zarządzanie trasami:** Wygenerowane trasy mają status tymczasowy do momentu świadomego zapisu przez użytkownika. Zapisane trasy będą miały automatycznie generowaną nazwę z możliwością jej zmiany przez użytkownika.
8.  **Edycja tras:** W ramach MVP użytkownik będzie mógł usunąć punkt z trasy przed jej zapisaniem. Edycja już zapisanych tras nie wchodzi w zakres MVP.
9.  **Tryb offline:** Raz załadowana trasa (mapa i opisy) będzie buforowana w przeglądarce, aby zapewnić dostęp w przypadku utraty połączenia z internetem.
10. **Ograniczenia:** Wprowadzony zostanie limit wyboru do 2-3 tagów przy generowaniu trasy. Trasa generowana przez AI będzie miała maksymalnie 7 punktów, a trasa manualna - 10.
11. **Lokalizacja:** Wersja MVP będzie dostępna wyłącznie w języku polskim (zarówno interfejs, jak i generowane treści).

\</decisions\>

\<matched\_recommendations\>

1.  **Sprecyzowanie metryk sukcesu:** Kluczowe kryterium sukcesu (70% akceptacji tras) będzie mierzone nie tylko przez kliknięcie przycisku "zapisz wycieczkę", ale również przez silniejszy wskaźnik – kliknięcie w przycisk "Nawiguj do" przy jakimkolwiek punkcie trasy.
2.  **Mechanizm zbierania feedbacku:** Wprowadzono dwupoziomowy system opinii: ocena (kciuk w górę/dół) dla każdego opisu miejsca oraz ogólna ocena (uśmiechnięta/smutna buźka) dla całej trasy, co pozwoli na iteracyjne ulepszanie algorytmu i jakości treści.
3.  **Obsługa niezalogowanych użytkowników:** Podjęto strategiczną decyzję o wymaganiu logowania/rejestracji przed skorzystaniem z funkcji generowania tras. Ma to na celu minimalizację kosztów związanych z API oraz ochronę przed zautomatyzowanymi atakami.
4.  **Uproszczenie procesu onboardingu:** Zrezygnowano z formalnego samouczka na rzecz przejrzystego interfejsu na stronie głównej, który intuicyjnie prowadzi użytkownika przez proces tworzenia trasy.
5.  **Automatyzacja w trybie manualnym:** W celu uproszczenia MVP, trasa w trybie manualnym będzie miała automatycznie optymalizowaną kolejność punktów, a funkcja ręcznego sortowania zostanie odłożona na przyszłość.
    \</matched\_recommendations\>

\<prd\_planning\_summary\>

### Podsumowanie Planowania PRD dla Pathie (MVP)

Celem projektu Pathie jest rozwiązanie problemu planowania spersonalizowanych, tematycznych wycieczek miejskich. Aplikacja będzie generować trasy z unikalnymi opisami miejsc, dopasowanymi do zainteresowań użytkownika.

**a. Główne wymagania funkcjonalne produktu:**

  * **System Kont:** Rejestracja i logowanie (e-mail/hasło, Google).
  * **Rdzeń Funkcjonalności - Generowanie Tras AI:**
      * Wybór 2-3 predefiniowanych tagów (zainteresowań) oraz opcjonalna opcja wprowadzenia tekstu opisującego wymagania co do tematu spaceru.
      * Generowanie trasy do 7 punktów na podstawie tagów i lokalizacji.
      * Tworzenie spersonalizowanych opisów dla każdego punktu w oparciu o dane z API Wikipedii, wybrane tagi i dodatkowy opis.
  * **Alternatywna Funkcjonalność - Tworzenie Manualne:**
      * Wyszukiwanie i dodawanie do 10 punktów na interaktywnej mapie.
      * Automatyczna optymalizacja kolejności dodanych punktów.
  * **Interakcja z Trasą:**
      * Wyświetlanie trasy na liście oraz na mapie.
      * Możliwość usunięcia punktu z trasy przed jej zapisaniem.
      * Funkcja "Nawiguj do" otwierająca zewnętrzną aplikację mapową.
      * Wyświetlanie pozycji użytkownika na mapie na żądanie.
  * **Zarządzanie Trasami Użytkownika:**
      * Zapisywanie, odczytywanie, przeglądanie i usuwanie tras.
      * Możliwość zmiany nazwy zapisanej trasy.
  * **System Feedbacku:**
      * Ocena "kciuk w górę/dół" dla każdego opisu.
      * Ogólna ocena "buźkami" dla całej wygenerowanej trasy.

**b. Kluczowe historie użytkownika i ścieżki korzystania:**

  * **Główna ścieżka (Odkrywca AI):** Użytkownik wchodzi na stronę, wybiera interesujące go tagi (np. "sztuka uliczna", "kuchnia"), inicjuje generowanie trasy. Przegląda zaproponowane punkty i opisy, akceptuje trasę, zapisuje ją na swoim koncie, a następnie rozpoczyna zwiedzanie, korzystając z przycisków nawigacji do poszczególnych punktów.
  * **Ścieżka alternatywna (Manualny Planista):** Użytkownik ma już listę konkretnych miejsc do odwiedzenia. Wybiera tryb manualny, wyszukuje i dodaje kolejne punkty na mapie. Aplikacja układa je w optymalnej kolejności. Użytkownik zapisuje trasę i korzysta z niej w ten sam sposób, co w ścieżce AI.

**c. Ważne kryteria sukcesu i sposoby ich mierzenia:**

  * **Kryterium 1: Akceptacja Tras (Cel: 70%)**
      * **Pomiar:** Procent wygenerowanych tras, które *nie zostały* odrzucone przez użytkownika (klknięcie "zapisz wycieczkę") ORAZ procent tras, na których użytkownik kliknął przycisk "Nawiguj do" przynajmniej raz.
  * **Kryterium 2: Jakość Treści (Cel: 70%)**
      * **Pomiar:** Procent opisów punktów na trasie, które otrzymały pozytywną ocenę (kciuk w górę) od użytkowników.

\</prd\_planning\_summary\>

\<unresolved\_issues\>
Na tym etapie planowania PRD nie zidentyfikowano żadnych krytycznych, nierozwiązanych kwestii. Główne funkcjonalności, założenia i ograniczenia MVP zostały zdefiniowane. Kolejne kroki powinny obejmować projektowanie szczegółowego interfejsu użytkownika (UX/UI) oraz tworzenie specyfikacji technicznej dla deweloperów.
\</unresolved\_issues\>
\</conversation\_summary\>