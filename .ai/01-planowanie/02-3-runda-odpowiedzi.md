Doskonale. Potwierdzenie tych założeń pozwoliło nam stworzyć solidny fundament dla MVP. Wszystkie kluczowe mechanizmy są już zdefiniowane. Nadszedł czas, aby skupić się na szczegółach dotyczących doświadczenia użytkownika (UX) i doprecyzować ostatnie niejasności, aby dokument PRD był kompletny.

Oto finałowa lista 10 pytań i zaleceń.

\<pytania\>

1.  Jak dokładnie preferencje użytkownika (np. tag "sztuka" vs "historia") wpłyną na treść generowanego opisu dla tego samego miejsca, np. Zamku Królewskiego? Czy AI ma skupiać się na konkretnych faktach, czy zmieniać ton i styl opisu?

Rekomendacja: Zdefiniujmy w promptach dla AI, że ma ono dostosować treść, wyciągając z materiału źródłowego (Wikipedia) fakty związane z wybranym tagiem. Dla "sztuki" skupi się na architekturze i zbiorach, dla "historii" na wydarzeniach i postaciach, zachowując neutralny, informacyjny ton w MVP.

Odpowiedź: Rekomendacja: Zdefiniujmy w promptach dla AI, że ma ono dostosować treść, wyciągając z materiału źródłowego (Wikipedia) fakty związane z wybranym tagiem. Dla "sztuki" skupi się na architekturze i zbiorach, dla "historii" na wydarzeniach i postaciach, zachowując neutralny, informacyjny ton w MVP.

2.  Jak będzie wyglądało pierwsze doświadczenie użytkownika (onboarding)? Czy po wejściu na stronę od razu przechodzi do tworzenia trasy, czy planujemy krótki samouczek lub ekran powitalny wyjaśniający wartość aplikacji?

Rekomendacja: Dla MVP zrezygnujmy z formalnego samouczka. Stwórzmy prosty i klarowny interfejs na stronie głównej, który od razu zachęca do akcji (np. "Wybierz swoje zainteresowania, aby stworzyć idealną trasę"), z minimalną ilością tekstu wyjaśniającego proces w 2-3 krokach.

Odpowiedź: Dla MVP zrezygnujmy z formalnego samouczka. Stwórzmy prosty i klarowny interfejs na stronie głównej, który od razu zachęca do akcji (np. "Wybierz swoje zainteresowania, aby stworzyć idealną trasę"), z minimalną ilością tekstu wyjaśniającego proces w 2-3 krokach.

3.  W jaki sposób będą prezentowane zapisane trasy na liście użytkownika? Jakie informacje będą widoczne na pierwszy rzut oka (np. nazwa, miasto, liczba punktów, główne tagi)? Czy użytkownik będzie mógł nadać trasie własną nazwę?

Rekomendacja: Na liście zapisanych tras wyświetlajmy automatycznie wygenerowaną nazwę (np. "Historyczny spacer po Warszawie"), główne tagi i liczbę punktów. Dodajmy prostą funkcję "Zmień nazwę", aby użytkownik mógł spersonalizować swoje wycieczki.

Odpowiedź: Na liście zapisanych tras wyświetlajmy automatycznie wygenerowaną nazwę (np. "Historyczny spacer po Warszawie"), główne tagi i liczbę punktów. Dodajmy prostą funkcję "Zmień nazwę", aby użytkownik mógł spersonalizować swoje wycieczki.

4.  Po wygenerowaniu, jak finalnie będzie zaprezentowana trasa? Czy będzie to interaktywna mapa z ponumerowanymi punktami i listą opisów obok, czy może widok przełączany między mapą a listą?

Rekomendacja: Zaprojektujmy widok dzielony (split-screen) na urządzeniach desktopowych: mapa z trasą po lewej, przewijana lista punktów z opisami po prawej. Na mobile'u domyślnym widokiem będzie lista, z przyciskiem przełączającym na pełnoekranową mapę.

Odpowiedź: Zaprojektujmy widok dzielony (split-screen) na urządzeniach desktopowych: mapa z trasą po lewej, przewijana lista punktów z opisami po prawej. Na mobile'u domyślnym widokiem będzie lista, z przyciskiem przełączającym na pełnoekranową mapę.

5.  W trybie manualnym, gdy użytkownik doda kilka punktów, czy będzie mógł samodzielnie ustalić ich kolejność (drag-and-drop), czy aplikacja automatycznie zoptymalizuje trasę przejścia między nimi?

Rekomendacja: W MVP uprośćmy proces: po dodaniu punktów przez użytkownika, aplikacja automatycznie ułoży je w logiczną, zoptymalizowaną pod kątem odległości trasę. Ręczne sortowanie to świetna funkcja na przyszłość.

Odpowiedź: W MVP uprośćmy proces: po dodaniu punktów przez użytkownika, aplikacja automatycznie ułoży je w logiczną, zoptymalizowaną pod kątem odległości trasę. Ręczne sortowanie to świetna funkcja na przyszłość.

6.  Co stanie się, gdy niezalogowany użytkownik stworzy trasę, a następnie kliknie "Zapisz"? Czy straci swoją pracę, czy pojawi się modal z prośbą o zalogowanie/rejestrację w celu zapisania postępu?

Rekomendacja: Zaimplementujmy przyjazny dla konwersji mechanizm. Po kliknięciu "Zapisz" przez gościa, wygenerowana trasa powinna zostać tymczasowo zapisana w sesji, a użytkownikowi powinno pojawić się okno logowania/rejestracji z komunikatem: "Załóż konto, aby zapisać swoją trasę i mieć do niej dostęp w przyszłości".

Odpowiedź: Zaimplementujmy przyjazny dla konwersji mechanizm. Po kliknięciu "Zapisz" przez gościa, wygenerowana trasa powinna zostać tymczasowo zapisana w sesji, a użytkownikowi powinno pojawić się okno logowania/rejestracji z komunikatem: "Załóż konto, aby zapisać swoją trasę i mieć do niej dostęp w przyszłości".

7.  Czy użytkownik, który zapisał już trasę na swoim koncie, będzie mógł ją później edytować (np. usunąć punkt, który odwiedził i mu się nie podobał)?

Rekomendacja: Funkcjonalność edycji zapisanych tras wykracza poza zakres MVP. Na tym etapie skupmy się na solidnym tworzeniu i odczytywaniu. Użytkownik, który chce zmodyfikować trasę, będzie musiał stworzyć nową.

Odpowiedź: Rekomendacja: Funkcjonalność edycji zapisanych tras wykracza poza zakres MVP. Na tym etapie skupmy się na solidnym tworzeniu i odczytywaniu. Użytkownik, który chce zmodyfikować trasę, będzie musiał stworzyć nową.


8.  Czy aplikacja w wersji MVP będzie skierowana wyłącznie do polskojęzycznych użytkowników i generowała treści tylko w języku polskim?

Rekomendacja: Skupmy się w 100% na języku polskim dla MVP – zarówno w interfejsie, jak i w treściach generowanych przez AI. Zapewni to wyższą jakość i spójność doświadczenia, a internacjonalizację można wprowadzić w przyszłości.

Odpowiedź: Skupmy się w 100% na języku polskim dla MVP – zarówno w interfejsie, jak i w treściach generowanych przez AI. Zapewni to wyższą jakość i spójność doświadczenia, a internacjonalizację można wprowadzić w przyszłości.


9.  Oprócz oceniania opisów (kciuk w górę/dół), czy przewidujemy mechanizm do zbierania opinii na temat jakości samej trasy (np. jej logiki, doboru miejsc)?

Rekomendacja: Na końcu każdej trasy (pod ostatnim punktem) dodajmy proste, opcjonalne pytanie: "Jak oceniasz tę trasę?" z dwiema ikonami (np. uśmiechnięta/smutna buźka). To da nam cenny, ogólny feedback na temat jakości algorytmu bez tworzenia skomplikowanych formularzy.

Odpowiedź: Na końcu każdej trasy (pod ostatnim punktem) dodajmy proste, opcjonalne pytanie: "Jak oceniasz tę trasę?" z dwiema ikonami (np. uśmiechnięta/smutna buźka). To da nam cenny, ogólny feedback na temat jakości algorytmu bez tworzenia skomplikowanych formularzy.

10. Czy definiujemy jakieś ograniczenia, np. maksymalną liczbę punktów w trasie manualnej lub maksymalną liczbę punktów, jaką AI może wygenerować dla pojedynczej wycieczki?

Rekomendacja: Ustalmy w MVP rozsądne limity, aby zapewnić wydajność i jakość: np. maksymalnie 15 punktów dla trasy manualnej i limit generowania przez AI do 10 punktów na jedną trasę. To zapobiegnie tworzeniu zbyt długich i niepraktycznych wycieczek.

Odpowiedź: Rekomendacja: Ustalmy w MVP rozsądne limity, aby zapewnić wydajność i jakość: np. maksymalnie 15 punktów dla trasy manualnej i limit generowania przez AI do 10 punktów na jedną trasę. To zapobiegnie tworzeniu zbyt długich i niepraktycznych wycieczek.
\</pytania\>