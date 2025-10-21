**Prompt:**

Jesteś sceptycznym, ale pragmatycznym ekspertem architektury oprogramowania, specjalizującym się w stosie **Django + Postgres + Docker**.

Stoję przed fundamentalnym dylematem dotyczącym zarządzania schematem bazy danych zdefiniowanym w <migracje> @migracje.sql </migracje>.
Z jednej strony, chcę korzystać z wygody ORM Django i systemu migracji (`models.py`, `makemigrations`) do zarządzania 90% schematu (tabelami, polami, kluczami obcymi).

Z drugiej strony, moja aplikacja **musi** implementować zaawansowane funkcje Postgresa, których ORM Django natywnie nie rozumie, takie jak **polityki RLS (Row-Level Security)** i triggery.

Wiem, że czyste podejście "Model-first" jest naiwne (bo jak zdefiniować RLS w `models.py`?), a czyste podejście "Database-first" (utrzymywanie ręcznego `schema.sql` i używanie `inspectdb`) jest archaiczne i zabija zalety systemu migracji Django.

Proszę, opisz **"najmniej złą" strategię hybrydową**, która pozwala pogodzić te dwa światy.

W swoim opisie wyjaśnij:

1.  **Podział odpowiedzialności**: Które elementy schematu powinny być definiowane w `models.py`, a które powinny być traktowane jako "nakładka SQL"?
2.  **Mechanizm implementacji**: Jak w praktyce włączyć ręczny kod SQL (np. `CREATE POLICY ...` lub `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`) do standardowego systemu migracji Django? Jakiej komendy i jakiej operacji (w pliku migracji) należy do tego użyć?
3.  **Proces wdrożenia (Deployment)**: Jak to hybrydowe podejście wpływa na proces wdrożenia w Docker Compose? Czy standardowe polecenie `docker-compose run --rm app python manage.py migrate` nadal jest poprawnym i wystarczającym sposobem na wdrożenie *całego* schematu (zarówno struktur z modeli, jak i polityk RLS)?
4.  **Wady i kompromisy**: Bądź sceptyczny – jakie są największe wady tego hybrydowego podejścia? (np. "rozmycie źródła prawdy", konieczność dyscypliny w zespole itp.).