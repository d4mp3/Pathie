<pytania>
1. Jak powinna być zorganizowana tabela "route_points" - czy powinna zawierać tylko kolejność czy także dodatkowe metadane?

A: Tabela "route_points" powinna zawierać pole "order" (kolejność), ale także pola "added_at" (czas dodania) i "is_removed" (boolean) dla śledzenia zmian w trasie tymczasowej, ponieważ użytkownicy mogą usuwać punkty przed zapisaniem trasy.

2. Czy należy przechowywać dane geograficzne punktów w osobnej tabeli "places" czy bezpośrednio w "points"?

A: Utworzyć osobną tabelę "places" z danymi geograficznymi i podstawowymi informacjami, a "points" powinna być tabelą pośrednią między "places" a "routes", ponieważ ten sam punkt geograficzny może być używany w różnych trasach.

3. Jak obsłużyć różne typy punktów - czy punkty z tras AI i manualnych powinny być w tej samej tabeli?

A: Tak, wszystkie punkty powinny być w jednej tabeli "points", ale dodać pole "source" (ai_generated/manual) dla rozróżnienia pochodzenia, ponieważ funkcjonalność jest identyczna niezależnie od źródła.

4. Czy opisy miejsc powinny być powiązane z punktami czy z kombinacją punkt+trasa?

A: Opisy powinny być powiązane z kombinacją punkt+trasa, ponieważ ten sam punkt może mieć różne opisy w zależności od kontekstu trasy (tagi zainteresowań)

5. Jak przechowywać dane sesji użytkownika dla tras tymczasowych?

A: rozwiń pytanie, prd nie zakłada możliwości dostępu aplikacji przez niezalogowanych użytkowników, trasy tymczasowe powinny być usuwane natychmiast po wyjściu z generatora jeśli nie zostaną one zapisane do bazy.

6. Czy należy utworzyć indeksy na pola geograficzne dla wydajności map?

A: Tak, należy utworzyć indeks przestrzenny (GIST) na pole geometryczne w tabeli "places" oraz indeksy na pola "latitude" i "longitude" dla szybkiego wyszukiwania w określonym obszarze.

7. Jak obsłużyć walidację limitów punktów w trasie (7 dla AI, 10 dla manualnych)?

A: Dodać pole "route_type" (ai_generated/manual) w tabeli "routes" i implementować walidację na poziomie aplikacji, ponieważ różne typy tras mają różne limity punktów.

8. Czy należy przechowywać metadane o generowaniu tras AI (czas generowania, użyte API)?

A: Tak, utworzyć tabelę "ai_generation_logs" z polami "route_id", "generation_time", "api_used", "tokens_used" dla analizy wydajności i kosztów AI, co jest ważne dla MVP.

9. Jak zorganizować system tagów - czy powinny być predefiniowane czy dynamiczne?

A: Tagi powinny być predefiniowane w tabeli "tags" z polami "name", "description", "is_active", "priority" ponieważ PRD wspomina o "predefiniowanych tagach zainteresowań" i potrzebie kontroli nad ich jakością.

10. Czy należy przechowywać historię ocen użytkowników czy tylko aktualne oceny?

A: Przechowywać tylko aktualne oceny w tabelach "description_ratings" i "route_ratings" z możliwością zmiany oceny, ponieważ PRD nie wymaga historii ocen, a to upraszcza implementację MVP.
</pytania>