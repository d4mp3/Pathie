## 1. Lista tabel z kolumnami, typami danych i ograniczeniami

### Tabela: `routes`
- `id` — bigint, PK
- `user_id` — bigint, FK → `auth_user(id)`, NOT NULL, ON DELETE CASCADE
- `name` — text, NOT NULL
- `status` — text, NOT NULL, CHECK (`status` IN ('temporary','saved'))
- `route_type` — text, NOT NULL, CHECK (`route_type` IN ('ai_generated','manual'))
- `saved_at` — timestamptz, NULL
- `cached_at` — timestamptz, NULL
- `cache_expires_at` — timestamptz, NULL
- `created_at` — timestamptz, NOT NULL, DEFAULT now()
- `updated_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- FK: (`user_id`) → `auth_user(id)` ON DELETE CASCADE

---

### Tabela: `places`
- `id` — bigint, PK
- `name` — text, NOT NULL
- `osm_id` — bigint, NULL, UNIQUE
- `wikipedia_id` — text, NULL, UNIQUE
- `address` — text, NULL
- `city` — text, NULL
- `country` — text, NULL
- `lat` — double precision, NOT NULL, CHECK (`lat` BETWEEN -90 AND 90)
- `lon` — double precision, NOT NULL, CHECK (`lon` BETWEEN -180 AND 180)
- `data` — jsonb, NULL  (np. zrzuty danych z OSM/Wikipedia)
- `created_at` — timestamptz, NOT NULL, DEFAULT now()
- `updated_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- Unikalność: (`osm_id`) UNIQUE, (`wikipedia_id`) UNIQUE

(Uwaga: pole geometrii PostGIS `geom geometry(Point,4326)` do dodania w przyszłości wraz z rozszerzeniem PostGIS.)

---

### Tabela: `route_points`
- `id` — bigint, PK
- `route_id` — bigint, FK → `routes(id)`, NOT NULL, ON DELETE CASCADE
- `place_id` — bigint, FK → `places(id)`, NOT NULL, ON DELETE CASCADE
- `source` — text, NOT NULL, CHECK (`source` IN ('ai_generated','manual'))
- `position` — integer, NOT NULL  (kolejność bazowa)
- `optimized_position` — integer, NULL  (kolejność po optymalizacji)
- `is_removed` — boolean, NOT NULL, DEFAULT false
- `added_at` — timestamptz, NOT NULL, DEFAULT now()
- `created_at` — timestamptz, NOT NULL, DEFAULT now()
- `updated_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- FK: (`route_id`) → `routes(id)` ON DELETE CASCADE
- FK: (`place_id`) → `places(id)` ON DELETE CASCADE

---

### Tabela: `place_descriptions`
- `id` — bigint, PK
- `route_point_id` — bigint, FK → `route_points(id)`, NOT NULL, UNIQUE, ON DELETE CASCADE
- `language_code` — varchar(8), NOT NULL, DEFAULT 'pl'
- `content` — text, NOT NULL, CHECK (char_length(`content`) BETWEEN 2500 AND 5000)
- `created_by_ai` — boolean, NOT NULL, DEFAULT true
- `created_at` — timestamptz, NOT NULL, DEFAULT now()
- `updated_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- FK: (`route_point_id`) → `route_points(id)` ON DELETE CASCADE
- 1:1 względem `route_points` dzięki UNIQUE(`route_point_id`)

---

### Tabela: `tags`
- `id` — bigint, PK
- `name` — text, NOT NULL, UNIQUE (case-insensitive przez indeks na `lower(name)`)
- `description` — text, NULL
- `is_active` — boolean, NOT NULL, DEFAULT true
- `priority` — integer, NOT NULL, DEFAULT 0
- `created_at` — timestamptz, NOT NULL, DEFAULT now()
- `updated_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- Unikalność logiczna: unikalny indeks na `lower(name)`

---

### Tabela: `route_tags`
- `route_id` — bigint, FK → `routes(id)`, NOT NULL, ON DELETE CASCADE
- `tag_id` — bigint, FK → `tags(id)`, NOT NULL, ON DELETE RESTRICT
- `created_at` — timestamptz, NOT NULL, DEFAULT now()

Klucze:
- PK: (`route_id`, `tag_id`)

---

### Tabela: `ratings`
- `id` — bigint, PK
- `user_id` — bigint, FK → `auth_user(id)`, NOT NULL, ON DELETE CASCADE
- `rating_type` — text, NOT NULL, CHECK (`rating_type` IN ('place_description','route'))
- `rating_value` — smallint, NOT NULL, CHECK (`rating_value` IN (-1, 1))
- `route_id` — bigint, NULL, FK → `routes(id)` ON DELETE CASCADE
- `place_description_id` — bigint, NULL, FK → `place_descriptions(id)` ON DELETE CASCADE
- `created_at` — timestamptz, NOT NULL, DEFAULT now()
- `updated_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- CHECK: dokładnie jedno z (`route_id`, `place_description_id`) jest NOT NULL i zgodne z `rating_type`:
  - gdy `rating_type='route'` → `route_id` NOT NULL i `place_description_id` NULL
  - gdy `rating_type='place_description'` → `place_description_id` NOT NULL i `route_id` NULL
- Jedna ocena użytkownika na cel (wymuszone unikalnością częściową — patrz sekcja Indeksy)

---

### Tabela: `ai_generation_logs`
- `id` — bigint, PK
- `route_id` — bigint, FK → `routes(id)`, NOT NULL, ON DELETE CASCADE
- `model` — text, NOT NULL
- `provider` — text, NULL
- `prompt_hash` — text, NULL
- `tags_snapshot` — text[], NOT NULL, DEFAULT '{}'
- `additional_text_snapshot` — text, NULL
- `points_count` — integer, NULL, CHECK (`points_count` BETWEEN 0 AND 7)
- `tokens_prompt` — integer, NULL, CHECK (`tokens_prompt` >= 0)
- `tokens_completion` — integer, NULL, CHECK (`tokens_completion` >= 0)
- `cost_usd` — numeric(10,4), NULL, CHECK (`cost_usd` >= 0)
- `request_id` — text, NULL
- `metadata` — jsonb, NULL
- `created_at` — timestamptz, NOT NULL, DEFAULT now()

Ograniczenia:
- FK: (`route_id`) → `routes(id)` ON DELETE CASCADE


## 2. Relacje między tabelami
- `auth_user (1) → (N) routes`
- `routes (1) → (N) route_points`
- `places (1) → (N) route_points`
- `route_points (1) → (1) place_descriptions`
- `routes (M) ↔ (N) tags` poprzez `route_tags`
- `routes (1) → (N) ai_generation_logs`
- `ratings`:
  - `auth_user (1) → (N) ratings`
  - `routes (1) → (N) ratings` gdy `rating_type='route'`
  - `place_descriptions (1) → (N) ratings` gdy `rating_type='place_description'`


## 3. Indeksy

### Ogólne i funkcjonalne
- `routes_idx_user_status_created`: btree (`user_id`, `status`, `created_at` DESC)
- `routes_idx_route_type`: btree (`route_type`)
- `route_points_idx_route_position`: btree (`route_id`, `position`)
- `route_points_idx_route_removed`: btree (`route_id`, `is_removed`)
- `route_points_uniq_position_active`: UNIQUE PARTIAL (`route_id`, `position`) WHERE `is_removed=false`
- `places_idx_lat_lon`: btree (`lat`, `lon`)
- `places_idx_name_address_fts`: GIN ON `to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(address,''))`
- `tags_uniq_lower_name`: UNIQUE btree ON `lower(name)`
- `route_tags_idx_tag`: btree (`tag_id`)
- `place_descriptions_idx_fts`: GIN ON `to_tsvector('simple', content)`
- `ratings_idx_user`: btree (`user_id`)
- `ratings_uniq_user_route`: UNIQUE PARTIAL (`user_id`, `route_id`) WHERE `rating_type='route'`
- `ratings_uniq_user_place_description`: UNIQUE PARTIAL (`user_id`, `place_description_id`) WHERE `rating_type='place_description'`
- `ai_generation_logs_idx_route_created`: btree (`route_id`, `created_at` DESC)

(Uwaga: po włączeniu PostGIS dodać `places_gist_geom`: GIST (`geom`) i ewentualne indeksy złożone przestrzenne.)


## 4. Zasady PostgreSQL (RLS i triggery)

### Założenia techniczne dla RLS
- Aplikacja ustawia w sesji identyfikator użytkownika: `select set_config('app.user_id', '<user_id>', true);`
- W politykach używamy: `current_setting('app.user_id', true)::bigint`

### Włączenie RLS
- `ALTER TABLE routes ENABLE ROW LEVEL SECURITY;`
- `ALTER TABLE route_points ENABLE ROW LEVEL SECURITY;`
- `ALTER TABLE place_descriptions ENABLE ROW LEVEL SECURITY;`
- `ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;`

### Polityki RLS (wzorce)
```sql
-- routes: tylko właściciel ma dostęp
CREATE POLICY routes_owner_select ON routes
  FOR SELECT USING (user_id = current_setting('app.user_id', true)::bigint);
CREATE POLICY routes_owner_modify ON routes
  FOR INSERT WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
CREATE POLICY routes_owner_update ON routes
  FOR UPDATE USING (user_id = current_setting('app.user_id', true)::bigint)
             WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
CREATE POLICY routes_owner_delete ON routes
  FOR DELETE USING (user_id = current_setting('app.user_id', true)::bigint);

-- route_points: dostęp pochodny od ownership trasy
CREATE POLICY route_points_owner ON route_points
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM routes r
      WHERE r.id = route_points.route_id
        AND r.user_id = current_setting('app.user_id', true)::bigint
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM routes r
      WHERE r.id = route_points.route_id
        AND r.user_id = current_setting('app.user_id', true)::bigint
    )
  );

-- place_descriptions: dostęp pochodny od ownership trasy przez route_points
CREATE POLICY place_descriptions_owner ON place_descriptions
  FOR ALL USING (
    EXISTS (
      SELECT 1
      FROM route_points rp
      JOIN routes r ON r.id = rp.route_id
      WHERE rp.id = place_descriptions.route_point_id
        AND r.user_id = current_setting('app.user_id', true)::bigint
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1
      FROM route_points rp
      JOIN routes r ON r.id = rp.route_id
      WHERE rp.id = place_descriptions.route_point_id
        AND r.user_id = current_setting('app.user_id', true)::bigint
    )
  );

-- ratings: użytkownik widzi i modyfikuje tylko swoje oceny
CREATE POLICY ratings_owner_select ON ratings
  FOR SELECT USING (user_id = current_setting('app.user_id', true)::bigint);
CREATE POLICY ratings_owner_modify ON ratings
  FOR ALL USING (user_id = current_setting('app.user_id', true)::bigint)
           WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
```

(Uwagi: dla raportowania/metryk dodać role administracyjne lub funkcje SECURITY DEFINER agregujące dane poza RLS.)

### Triggery i funkcje pomocnicze

Aktualizacja `updated_at` na UPDATE (dla wszystkich głównych tabel):
```sql
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_routes BEFORE UPDATE ON routes
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_places BEFORE UPDATE ON places
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_route_points BEFORE UPDATE ON route_points
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_place_descriptions BEFORE UPDATE ON place_descriptions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_tags BEFORE UPDATE ON tags
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_ratings BEFORE UPDATE ON ratings
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

Limit tagów na trasę (1–3) — wymuszane deferralem w `route_tags`:
```sql
CREATE OR REPLACE FUNCTION enforce_route_tags_limit() RETURNS trigger AS $$
DECLARE cnt int;
BEGIN
  SELECT count(*) INTO cnt FROM route_tags WHERE route_id = NEW.route_id;
  IF TG_OP IN ('INSERT','UPDATE') THEN
    IF cnt < 1 THEN
      RAISE EXCEPTION 'Route must have at least 1 tag';
    ELSIF cnt > 3 THEN
      RAISE EXCEPTION 'Route must not have more than 3 tags';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER route_tags_limit
AFTER INSERT OR DELETE OR UPDATE ON route_tags
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_route_tags_limit();
```

Limit punktów na trasie wg typu (AI: ≤7, manual: ≤10) — na `route_points`:
```sql
CREATE OR REPLACE FUNCTION enforce_route_points_limit() RETURNS trigger AS $$
DECLARE cnt int; r_type text;
BEGIN
  SELECT route_type INTO r_type FROM routes WHERE id = NEW.route_id;
  SELECT count(*) INTO cnt FROM route_points
   WHERE route_id = NEW.route_id AND is_removed = false;

  IF r_type = 'ai_generated' AND cnt > 7 THEN
    RAISE EXCEPTION 'AI-generated routes must have at most 7 points';
  ELSIF r_type = 'manual' AND cnt > 10 THEN
    RAISE EXCEPTION 'Manual routes must have at most 10 points';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER route_points_limit_insert
AFTER INSERT ON route_points
FOR EACH ROW EXECUTE FUNCTION enforce_route_points_limit();

CREATE TRIGGER route_points_limit_update
AFTER UPDATE OF is_removed ON route_points
FOR EACH ROW EXECUTE FUNCTION enforce_route_points_limit();
```

Wymuszenie spójności `ratings` (jedno pole celu NOT NULL zgodnie z typem) — CHECK już zdefiniowany; dodatkowo unikalność:
```sql
CREATE UNIQUE INDEX ratings_unique_user_route
  ON ratings(user_id, route_id)
  WHERE rating_type = 'route';

CREATE UNIQUE INDEX ratings_unique_user_place_desc
  ON ratings(user_id, place_description_id)
  WHERE rating_type = 'place_description';
```

Utrzymanie unikalnej pozycji aktywnych punktów w trasie:
```sql
CREATE UNIQUE INDEX route_points_unique_active_position
  ON route_points(route_id, position)
  WHERE is_removed = false;
```


## 5. Dodatkowe uwagi i wyjaśnienia
- Zgodność z Django: klucz obcy do `auth_user(id)` zakłada domyślny typ PK (bigint w nowszych projektach). W razie innej konfiguracji należy dostosować typ `user_id`.
- PostGIS: obecnie używamy `lat`/`lon` oraz indeksów btree; po włączeniu PostGIS dodać kolumnę `geom geometry(Point,4326)` i indeks GIST.
- Wyszukiwanie pełnotekstowe: użyto konfiguracji `'simple'` dla prostoty. Dla języka polskiego można rozważyć słownik `'polish'` (wymaga konfiguracji).
- Usuwanie tras tymczasowych i punktów odbywa się fizycznie (CASCADE). Okresowe czyszczenie „temporary” pozostaje po stronie aplikacji/CRON.
- Ograniczenia długości opisów (2500–5000 znaków) są zabezpieczone CHECK w `place_descriptions`.
- W `route_points` kolumny `position` i `optimized_position` umożliwiają zarówno bazową kolejność, jak i kolejność po optymalizacji; częściowy indeks unikalny zapewnia brak duplikatów pozycji w aktywnej trasie.
- System ocen scala różne typy ocen w jednej tabeli `ratings`, z częściowymi indeksami unikalnymi zapobiegającymi wielokrotnemu głosowaniu na ten sam obiekt przez tego samego użytkownika.
- Triggery `DEFERRABLE INITIALLY DEFERRED` dla limitów tagów pozwalają na poprawne działanie w obrębie jednej transakcji (najpierw INSERT tagów, weryfikacja na końcu).
- Wszystkie główne tabele posiadają `created_at`/`updated_at` i wspólny trigger `set_updated_at()` dla spójności audytu.