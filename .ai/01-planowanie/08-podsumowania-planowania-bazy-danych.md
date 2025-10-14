<conversation_summary>
<decisions>
1. Jedna tabela "routes" z polem "status" (temporary/saved) zamiast osobnych tabel dla tras tymczasowych i zapisanych
2. Tabela "route_points" zawiera pola "order", "added_at", "is_removed" oraz "optimized_order" dla śledzenia zmian i optymalizacji
3. Osobna tabela "places" z danymi geograficznymi i integracją z zewnętrznymi API (osm_id, wikipedia_id)
4. Tabela "points" jako pośrednia między "places" a "routes" z polem "source" (ai_generated/manual)
5. Opisy miejsc powiązane z kombinacją punkt+trasa w tabeli "place_descriptions"
6. Trasy tymczasowe usuwane natychmiast po wyjściu z generatora jeśli nie zostaną zapisane
7. Pole "route_type" (ai_generated/manual) w tabeli "routes" dla walidacji limitów punktów
8. Tabela "ai_generation_logs" dla metadanych generowania AI
9. Predefiniowane tagi w tabeli "tags" z polami "name", "description", "is_active", "priority"
10. Jedna tabela "ratings" z polami "rating_type" i "rating_value" dla wszystkich typów ocen
11. Brak rozróżnienia między nazwami automatycznie wygenerowanymi a edytowanymi przez użytkownika
12. Brak historii zmian tras w MVP
13. Buforowanie offline przez pola "cached_at" i "cache_expires_at" w istniejących tabelach
14. Fizyczne usuwanie tras z CASCADE rules zamiast soft delete
15. Brak backup strategy w fazie MVP
</decisions>

<matched_recommendations>
1. Relacja jeden-do-wielu między użytkownikami a trasami
2. Relacja wiele-do-wielu między punktami a trasami przez tabelę pośrednią z kolejnością
3. Indeksy geograficzne (GIST) i pełnotekstowe (GIN) dla wydajności
4. RLS na tabelach prywatnych użytkowników
5. CHECK constraints dla walidacji długości opisów i zakresów danych
6. Triggers dla automatycznego aktualizowania "updated_at"
7. Indeksy złożone dla często używanych kombinacji pól
8. Widoki PostgreSQL dla często używanych zapytań
9. Pola audytowe (created_at, updated_at) we wszystkich głównych tabelach
10. Przygotowanie struktury dla przyszłej integracji z PostGIS
</matched_recommendations>

<database_planning_summary>
## Główne wymagania dotyczące schematu bazy danych

Aplikacja Pathie MVP wymaga schematu bazy danych obsługującego:
- System kont użytkowników z uwierzytelnianiem lokalnym i Google OAuth
- Generowanie tras przez AI (maksymalnie 7 punktów) i tworzenie manualne (maksymalnie 10 punktów)
- Spersonalizowane opisy miejsc generowane przez AI (2500-5000 znaków)
- System ocen dla opisów i tras
- Buforowanie offline dla załadowanych tras
- Integrację z zewnętrznymi API (OpenStreetMap, Wikipedia)

## Kluczowe encje i ich relacje

**Główne tabele:**
- `users` - konta użytkowników (Django Auth)
- `routes` - trasy z polami status (temporary/saved) i route_type (ai_generated/manual)
- `places` - miejsca geograficzne z danymi z OSM i Wikipedii
- `route_points` - relacja wiele-do-wielu między routes i places z kolejnością
- `place_descriptions` - opisy miejsc powiązane z kombinacją punkt+trasa
- `tags` - predefiniowane tagi zainteresowań
- `route_tags` - relacja wiele-do-wielu między routes i tags
- `ratings` - oceny dla opisów i tras
- `ai_generation_logs` - metadane generowania AI

**Relacje kluczowe:**
- User → Routes (1:N)
- Routes ↔ Places (M:N przez route_points)
- Routes ↔ Tags (M:N przez route_tags)
- Place + Route → Place_Descriptions (1:1)
- Routes → AI_Generation_Logs (1:N)

## Ważne kwestie dotyczące bezpieczeństwa i skalowalności

**Bezpieczeństwo:**
- RLS na tabelach routes, route_points, place_descriptions, ratings
- CHECK constraints dla walidacji długości opisów (2500-5000 znaków)
- Walidacja zakresów współrzędnych geograficznych
- Ograniczenia liczby tagów (1-3) na trasę

**Wydajność:**
- Indeksy geograficzne (GIST) na pole geometry w places
- Indeksy pełnotekstowe (GIN) na name i address w places
- Indeksy złożone na (user_id, status, created_at) w routes
- Indeks złożony na (route_id, order) w route_points
- Widok "route_details" dla często używanych zapytań

**Skalowalność:**
- Struktura przygotowana na PostGIS (pole geometry w places)
- Triggers dla automatycznego aktualizowania updated_at
- Fizyczne usuwanie z CASCADE rules dla prostoty
- Brak partycjonowania w MVP (niepotrzebne przy małej skali)
</database_planning_summary>

<unresolved_issues>
1. Szczegółowa implementacja RLS rules - wymaga dokładnego określenia logiki dostępu
2. Strategia czyszczenia tras tymczasowych - czy automatyczne po określonym czasie?
3. Konkretne wartości dla indeksów i ich optymalizacja pod kątem rzeczywistych zapytań
4. Szczegóły integracji z zewnętrznymi API - format przechowywania danych z OSM i Wikipedii
5. Strategia migracji danych przy aktualizacjach schematu w środowisku produkcyjnym
</unresolved_issues>
</conversation_summary>