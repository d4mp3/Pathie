<pytania>
1. Jak zorganizować tabelę "places" - czy powinna zawierać tylko podstawowe dane geograficzne czy także informacje z zewnętrznych API?

A: Tabela "places" powinna zawierać podstawowe dane (nazwa, współrzędne, adres) oraz pola "osm_id" i "wikipedia_id" dla integracji z zewnętrznymi API, ponieważ aplikacja wykorzystuje dane z OpenStreetMap i Wikipedii do generowania opisów.

2. Czy należy utworzyć osobną tabelę dla buforowania danych offline czy wykorzystać istniejące tabele?

A: Wykorzystać istniejące tabele z dodatkowymi polami "cached_at" i "cache_expires_at" w tabeli "routes", ponieważ buforowanie offline dotyczy już istniejących tras, a nie wymaga osobnej struktury danych.

3. Jak obsłużyć automatyczną optymalizację kolejności punktów w trasach manualnych?

A: Dodać pole "optimized_order" w tabeli "route_points" oraz pole "is_optimized" w tabeli "routes", ponieważ użytkownicy mogą dodawać punkty w dowolnej kolejności, ale system musi automatycznie je zoptymalizować.

4. Czy należy przechowywać informacje o źródłach danych użytych do generowania opisów?

A: Tak, dodać pola "wikipedia_source" i "osm_source" w tabeli "place_descriptions

5. Jak zorganizować system ocen - czy jedna tabela dla wszystkich typów ocen czy osobne tabele?

A: Utworzyć osobną tabelę "ratings" z polami "rating_type" (description/route), "rating_value" (positive/negative)

6. Czy należy dodać pola audytowe (created_at, updated_at) do wszystkich głównych tabel?

A: Tak, dodać pola "created_at" i "updated_at" do wszystkich głównych tabel (routes, places, route_points, place_descriptions), ponieważ są przydatne do debugowania, analizy i przyszłych funkcji audytu.

7. Jak obsłużyć walidację długości opisów miejsc (2500-5000 znaków)?

A: Dodać ograniczenia na poziomie bazy danych (CHECK constraint) oraz walidację w Django, ponieważ PRD wyraźnie określa zakres długości opisów jako wymaganie funkcjonalne.

8. Czy należy utworzyć indeksy na pola tekstowe dla wyszukiwania miejsc?

A: Tak, utworzyć indeksy pełnotekstowe (GIN) na pola "name" i "address" w tabeli "places", ponieważ aplikacja wymaga wyszukiwania miejsc przez użytkowników w trybie manualnym.

9. Jak obsłużyć relację między tagami a trasami - czy potrzebna jest tabela pośrednia?

A: Tak, utworzyć tabelę "route_tags" z relacją wiele-do-wielu między "routes" i "tags", ponieważ użytkownicy mogą wybierać 1-3 tagi, a te same tagi mogą być używane w różnych trasach.

10. Czy należy dodać pola dla przyszłej integracji z PostGIS?

A: Tak, dodać pole "geometry" typu GEOMETRY w tabeli "places" obok pól "latitude" i "longitude", ponieważ tech stack wspomina o PostGIS jako przyszłej funkcjonalności, a migracja będzie łatwiejsza z przygotowaną strukturą.
</pytania>