## Schemat bazy danych PostgreSQL — Pathie (MVP)

### 1. Lista tabel (kolumny, typy, ograniczenia)

Uwaga: Tabela użytkowników pochodzi z Django (`auth_user`) i nie jest tu definiowana. Wszystkie FKi do użytkownika wskazują na `auth_user(id)` (INTEGER/BIGINT zależnie od konfiguracji Django).

```sql
-- Opcjonalnie (przygotowanie pod PostGIS)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- Pomocnicza funkcja do RLS: odczyt bieżącego user_id z ustawienia sesji
CREATE SCHEMA IF NOT EXISTS app;
CREATE OR REPLACE FUNCTION app.current_user_id()
RETURNS integer LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::integer;
$$;

-- Uniwersalny trigger do aktualizacji updated_at
CREATE OR REPLACE FUNCTION app.set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;$$;
```

#### 1.1. `places` — miejsca geograficzne (OSM, Wikipedia)
```sql
CREATE TABLE IF NOT EXISTS places (
  id                BIGSERIAL PRIMARY KEY,
  name              TEXT NOT NULL,
  display_name      TEXT,
  address           TEXT,
  city              TEXT,
  country_code      VARCHAR(2),
  -- Koordynaty (MVP bez PostGIS); przygotowane CHECK
  latitude          NUMERIC(9,6) NOT NULL,
  longitude         NUMERIC(9,6) NOT NULL,
  -- OSM identyfikator (typ + id); unikalność warunkowa
  osm_type          TEXT CHECK (osm_type IN ('node','way','relation')),
  osm_id            BIGINT,
  -- Wikipedia identyfikator (np. pl:Zamek_Królewski_w_Warszawie)
  wikipedia_lang    TEXT,
  wikipedia_title   TEXT,
  -- PostGIS (opcjonalnie)
  geom              geometry(Point, 4326),

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT places_latitude_range  CHECK (latitude  BETWEEN -90  AND 90),
  CONSTRAINT places_longitude_range CHECK (longitude BETWEEN -180 AND 180),
  CONSTRAINT places_osm_unique UNIQUE (osm_type, osm_id)
    DEFERRABLE INITIALLY IMMEDIATE,
  CONSTRAINT places_wikipedia_unique UNIQUE (wikipedia_lang, wikipedia_title)
    DEFERRABLE INITIALLY IMMEDIATE
);
CREATE TRIGGER trg_places_set_updated_at
  BEFORE UPDATE ON places FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
```

#### 1.2. `routes` — trasy (tymczasowe i zapisane)
```sql
CREATE TABLE IF NOT EXISTS routes (
  id                BIGSERIAL PRIMARY KEY,
  user_id           INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'temporary'
                     CHECK (status IN ('temporary','saved')),
  route_type        TEXT NOT NULL
                     CHECK (route_type IN ('ai_generated','manual')),

  -- Buforowanie offline (MVP)
  cached_at         TIMESTAMPTZ,
  cache_expires_at  TIMESTAMPTZ,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_routes_set_updated_at
  BEFORE UPDATE ON routes FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
```

#### 1.3. `route_points` — punkty trasy (kolejność, źródło)
```sql
CREATE TABLE IF NOT EXISTS route_points (
  id                BIGSERIAL PRIMARY KEY,
  route_id          BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  place_id          BIGINT NOT NULL REFERENCES places(id) ON DELETE RESTRICT,
  source            TEXT NOT NULL CHECK (source IN ('ai_generated','manual')),

  "order"          INTEGER NOT NULL CHECK ("order" >= 1),
  optimized_order   INTEGER CHECK (optimized_order IS NULL OR optimized_order >= 1),
  is_removed        BOOLEAN NOT NULL DEFAULT false,
  added_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT route_points_order_unique UNIQUE (route_id, "order")
);
```

#### 1.4. `place_descriptions` — spersonalizowane opisy miejsc (AI)
```sql
CREATE TABLE IF NOT EXISTS place_descriptions (
  id                BIGSERIAL PRIMARY KEY,
  route_id          BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  place_id          BIGINT NOT NULL REFERENCES places(id) ON DELETE CASCADE,

  content           TEXT,
  -- Długość opisu zgodna z PRD: 2500–5000 znaków (jeśli opis istnieje)
  CONSTRAINT place_desc_length_chk
    CHECK (content IS NULL OR (char_length(content) BETWEEN 2500 AND 5000)),

  -- Kontekst tagów użytych przy generowaniu (do śledzenia)
  context_tags      TEXT[] DEFAULT '{}',

  -- Buforowanie/offline
  cached_at         TIMESTAMPTZ,
  cache_expires_at  TIMESTAMPTZ,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- 1:1 dla kombinacji (route, place)
  CONSTRAINT place_descriptions_unique UNIQUE (route_id, place_id)
);
CREATE TRIGGER trg_place_descriptions_set_updated_at
  BEFORE UPDATE ON place_descriptions FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
```

#### 1.5. `tags` — predefiniowane tagi zainteresowań
```sql
CREATE TABLE IF NOT EXISTS tags (
  id                SERIAL PRIMARY KEY,
  slug              TEXT NOT NULL UNIQUE,
  name              TEXT NOT NULL,
  description       TEXT,
  is_active         BOOLEAN NOT NULL DEFAULT true,
  priority          INTEGER NOT NULL DEFAULT 0,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_tags_set_updated_at
  BEFORE UPDATE ON tags FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
```

#### 1.6. `route_tags` — M:N między trasami i tagami; limit 1–3 tagów/trasa
```sql
CREATE TABLE IF NOT EXISTS route_tags (
  route_id          BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  tag_id            INTEGER NOT NULL REFERENCES tags(id) ON DELETE RESTRICT,
  PRIMARY KEY (route_id, tag_id)
);
```

#### 1.7. `ratings` — oceny opisów i tras (jeden typ tabeli)
```sql
CREATE TABLE IF NOT EXISTS ratings (
  id                    BIGSERIAL PRIMARY KEY,
  user_id               INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
  rating_type           TEXT NOT NULL CHECK (rating_type IN ('place_description','route')),
  rating_value          SMALLINT NOT NULL CHECK (rating_value IN (-1, 1)),

  route_id              BIGINT REFERENCES routes(id) ON DELETE CASCADE,
  place_description_id  BIGINT REFERENCES place_descriptions(id) ON DELETE CASCADE,

  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Dokładnie jeden obiekt oceniany; spójność z typem
  CONSTRAINT ratings_target_chk CHECK (
    (rating_type = 'route' AND route_id IS NOT NULL AND place_description_id IS NULL) OR
    (rating_type = 'place_description' AND place_description_id IS NOT NULL AND route_id IS NULL)
  )
);
```

#### 1.8. `ai_generation_logs` — metadane generowania AI
```sql
CREATE TABLE IF NOT EXISTS ai_generation_logs (
  id                BIGSERIAL PRIMARY KEY,
  route_id          BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  user_id           INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,

  provider          TEXT NOT NULL,          -- np. openrouter
  model             TEXT NOT NULL,          -- np. gpt-4o-mini
  status            TEXT NOT NULL CHECK (status IN ('started','succeeded','failed')),
  error_message     TEXT,

  input_params      JSONB,                  -- prompt, tagi, lokalizacja itp.
  response_meta     JSONB,                  -- surowe metadane odpowiedzi (id żądania, usage)

  prompt_tokens     INTEGER,
  completion_tokens INTEGER,
  cost_usd          NUMERIC(12,6),
  duration_ms       INTEGER,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### 2. Relacje między tabelami (kardynalność)

- `auth_user (1) → (N) routes`
- `routes (M) ↔ (N) tags` przez `route_tags`
- `routes (1) → (N) route_points`
- `places (1) → (N) route_points`
- `routes (1) → (N) place_descriptions` (1:1 per `(route_id, place_id)`)
- `place_descriptions (1) ← (N) ratings` dla `rating_type='place_description'`
- `routes (1) ← (N) ratings` dla `rating_type='route'`
- `routes (1) → (N) ai_generation_logs`, `auth_user (1) → (N) ai_generation_logs`

Kardynalność i spójność kluczy są egzekwowane przez klucze obce i ograniczenia unikalności opisane powyżej.

---

### 3. Indeksy (wydajność zapytań)

```sql
-- routes
CREATE INDEX IF NOT EXISTS idx_routes_user_status_created
  ON routes (user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_routes_user_created
  ON routes (user_id, created_at DESC);

-- route_points
CREATE INDEX IF NOT EXISTS idx_route_points_route
  ON route_points (route_id);
CREATE INDEX IF NOT EXISTS idx_route_points_route_optimized
  ON route_points (route_id, optimized_order);
CREATE INDEX IF NOT EXISTS idx_route_points_place
  ON route_points (place_id);
CREATE INDEX IF NOT EXISTS idx_route_points_route_is_removed_partial
  ON route_points (route_id, "order") WHERE is_removed = false;

-- places: pełnotekstowy i geograficzny
CREATE INDEX IF NOT EXISTS idx_places_fulltext
  ON places USING GIN (to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(address,'')));
-- Jeśli PostGIS dostępny
-- CREATE INDEX IF NOT EXISTS idx_places_geom ON places USING GIST (geom);

-- place_descriptions
CREATE INDEX IF NOT EXISTS idx_place_desc_route
  ON place_descriptions (route_id);
CREATE INDEX IF NOT EXISTS idx_place_desc_place
  ON place_descriptions (place_id);

-- route_tags
CREATE INDEX IF NOT EXISTS idx_route_tags_tag ON route_tags (tag_id);

-- ratings: unikalność użytkownika per cel (partycje warunkowe)
CREATE UNIQUE INDEX IF NOT EXISTS uq_ratings_user_route
  ON ratings (user_id, route_id)
  WHERE rating_type = 'route';
CREATE UNIQUE INDEX IF NOT EXISTS uq_ratings_user_place_desc
  ON ratings (user_id, place_description_id)
  WHERE rating_type = 'place_description';
CREATE INDEX IF NOT EXISTS idx_ratings_route ON ratings (route_id);
CREATE INDEX IF NOT EXISTS idx_ratings_place_desc ON ratings (place_description_id);
CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings (user_id);

-- ai_generation_logs
CREATE INDEX IF NOT EXISTS idx_ai_logs_route_created
  ON ai_generation_logs (route_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_logs_user_created
  ON ai_generation_logs (user_id, created_at DESC);
```

---

### 4. Zasady PostgreSQL (RLS)

Polityki RLS zakładają, że aplikacja (Django) ustawia `SET app.current_user_id = '<id>'` dla każdej sesji/połączenia. W przeciwnym razie `app.current_user_id()` zwraca `NULL` i dostęp będzie odrzucony.

```sql
-- ROUTES
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
-- Właściciel może wszystko na swoich trasach
CREATE POLICY routes_owner_select ON routes
  FOR SELECT USING (user_id = app.current_user_id());
CREATE POLICY routes_owner_modify ON routes
  FOR ALL USING (user_id = app.current_user_id())
  WITH CHECK (user_id = app.current_user_id());

-- ROUTE_POINTS (dziedziczy własność z routes)
ALTER TABLE route_points ENABLE ROW LEVEL SECURITY;
CREATE POLICY route_points_owner_select ON route_points
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM routes r WHERE r.id = route_points.route_id AND r.user_id = app.current_user_id())
  );
CREATE POLICY route_points_owner_modify ON route_points
  FOR ALL USING (
    EXISTS (SELECT 1 FROM routes r WHERE r.id = route_points.route_id AND r.user_id = app.current_user_id())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM routes r WHERE r.id = route_points.route_id AND r.user_id = app.current_user_id())
  );

-- PLACE_DESCRIPTIONS (własność przez powiązaną trasę)
ALTER TABLE place_descriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY place_desc_owner_select ON place_descriptions
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM routes r WHERE r.id = place_descriptions.route_id AND r.user_id = app.current_user_id())
  );
CREATE POLICY place_desc_owner_modify ON place_descriptions
  FOR ALL USING (
    EXISTS (SELECT 1 FROM routes r WHERE r.id = place_descriptions.route_id AND r.user_id = app.current_user_id())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM routes r WHERE r.id = place_descriptions.route_id AND r.user_id = app.current_user_id())
  );

-- RATINGS: dostęp tylko do własnych ocen (prywatność w MVP)
ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;
CREATE POLICY ratings_owner_select ON ratings
  FOR SELECT USING (user_id = app.current_user_id());
CREATE POLICY ratings_owner_modify ON ratings
  FOR ALL USING (user_id = app.current_user_id())
  WITH CHECK (user_id = app.current_user_id());

-- AI GENERATION LOGS: dostęp właściciela
ALTER TABLE ai_generation_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_logs_owner_select ON ai_generation_logs
  FOR SELECT USING (user_id = app.current_user_id());
CREATE POLICY ai_logs_owner_modify ON ai_generation_logs
  FOR ALL USING (user_id = app.current_user_id())
  WITH CHECK (user_id = app.current_user_id());

-- Publiczne tabele bez RLS: places, tags, route_tags (odczyt publiczny)
-- (Ewentualne ograniczenia zapisu egzekwowane na poziomie aplikacji/admina)
```

---

### 5. Triggery biznesowe (walidacja reguł z PRD)

```sql
-- Limit liczby punktów na trasę:
--  - ai_generated: max 7
--  - manual:       max 10
CREATE OR REPLACE FUNCTION app.enforce_route_point_limits()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_route_type TEXT;
  v_count      INTEGER;
  v_limit      INTEGER;
BEGIN
  SELECT route_type INTO v_route_type FROM routes WHERE id = NEW.route_id;
  IF v_route_type IS NULL THEN
    RAISE EXCEPTION 'Route %% not found', NEW.route_id;
  END IF;

  v_limit := CASE WHEN v_route_type = 'ai_generated' THEN 7 ELSE 10 END;

  SELECT COUNT(*) INTO v_count
  FROM route_points
  WHERE route_id = NEW.route_id AND is_removed = false;

  IF v_count >= v_limit THEN
    RAISE EXCEPTION 'Point limit exceeded for route type %: limit %', v_route_type, v_limit;
  END IF;

  RETURN NEW;
END;$$;

DROP TRIGGER IF EXISTS trg_route_points_limit ON route_points;
CREATE TRIGGER trg_route_points_limit
  BEFORE INSERT ON route_points
  FOR EACH ROW EXECUTE FUNCTION app.enforce_route_point_limits();

-- Limit tagów 1..3 per route (egzekwowany przy INSERT/DELETE)
CREATE OR REPLACE FUNCTION app.enforce_route_tags_limits()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_count INTEGER;
BEGIN
  IF TG_OP = 'INSERT' THEN
    SELECT COUNT(*) INTO v_count FROM route_tags WHERE route_id = NEW.route_id;
    IF v_count >= 3 THEN
      RAISE EXCEPTION 'Tag limit exceeded (max 3) for route %', NEW.route_id;
    END IF;
  ELSIF TG_OP = 'DELETE' THEN
    SELECT COUNT(*) INTO v_count FROM route_tags WHERE route_id = OLD.route_id;
    IF v_count <= 1 THEN
      RAISE EXCEPTION 'At least 1 tag required for route %', OLD.route_id;
    END IF;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;$$;

DROP TRIGGER IF EXISTS trg_route_tags_limits_ins ON route_tags;
CREATE TRIGGER trg_route_tags_limits_ins
  BEFORE INSERT ON route_tags
  FOR EACH ROW EXECUTE FUNCTION app.enforce_route_tags_limits();

DROP TRIGGER IF EXISTS trg_route_tags_limits_del ON route_tags;
CREATE TRIGGER trg_route_tags_limits_del
  BEFORE DELETE ON route_tags
  FOR EACH ROW EXECUTE FUNCTION app.enforce_route_tags_limits();
```

---

### 6. Widoki (opcjonalnie, do częstych zapytań)

```sql
CREATE OR REPLACE VIEW route_details AS
SELECT
  r.id                      AS route_id,
  r.user_id,
  r.name,
  r.status,
  r.route_type,
  r.created_at,
  r.updated_at,
  -- Lista punktów w kolejności
  (
    SELECT jsonb_agg(
             jsonb_build_object(
               'route_point_id', rp.id,
               'order', rp."order",
               'optimized_order', rp.optimized_order,
               'is_removed', rp.is_removed,
               'added_at', rp.added_at,
               'place', jsonb_build_object(
                 'id', p.id,
                 'name', p.name,
                 'latitude', p.latitude,
                 'longitude', p.longitude,
                 'city', p.city
               ),
               'description', (
                 SELECT jsonb_build_object(
                          'id', pd.id,
                          'length', CASE WHEN pd.content IS NULL THEN 0 ELSE char_length(pd.content) END,
                          'has_content', (pd.content IS NOT NULL)
                        )
                 FROM place_descriptions pd
                 WHERE pd.route_id = r.id AND pd.place_id = rp.place_id
               )
             ) ORDER BY rp."order"
           )
    FROM route_points rp
    JOIN places p ON p.id = rp.place_id
    WHERE rp.route_id = r.id AND rp.is_removed = false
  ) AS points
FROM routes r;
```

---

### 7. Dodatkowe uwagi projektowe

- Indeksy są dobrane pod najczęstsze ścieżki zapytań: listy tras per użytkownik, pobranie szczegółów trasy (punkty + opisy), wyszukiwanie miejsc.
- RLS wymaga ustawienia `SET app.current_user_id = '<int>';` dla każdej sesji bazy — zrób to w warstwie połączeń (np. middleware Django).
- `place_descriptions.content` może być `NULL` dla tras manualnych; ograniczenie długości działa tylko gdy treść istnieje.
- Czyszczenie tras tymczasowych realizowane po stronie aplikacji (MVP); w razie potrzeby można dodać `expires_at` i job czyszczący.
- Fizyczne usuwanie (`ON DELETE CASCADE`) upraszcza model w MVP; rozbudowana historia zmian jest poza zakresem.
- Przy wdrożeniu PostGIS włączyć rozszerzenie i indeks `GIST (geom)`; w MVP operujemy na `latitude/longitude` i indeksach tekstowych.
- Wszystkie tabele mają pola audytowe `created_at/updated_at`; aktualizacja `updated_at` przez wspólny trigger.
