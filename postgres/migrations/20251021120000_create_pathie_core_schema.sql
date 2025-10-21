-- ============================================================================
-- Migration: Create Pathie Core Schema
-- ============================================================================
-- Purpose: Initial schema creation for Pathie application including:
--          - Core tables (places, routes, tags, ratings, etc.)
--          - Full-text search indexes
--          - Row Level Security (RLS) policies
--          - Business logic constraints (route points limit, tags limit)
--          - Audit triggers for updated_at fields
--
-- Affected tables: places, tags, routes, route_points, place_descriptions,
--                  route_tags, ratings, ai_generation_logs
--
-- Special notes:
--   - Assumes auth_user table exists (Django default user model)
--   - RLS uses session variable 'app.user_id' set by Django application
--   - PostGIS geometry columns will be added in future migration
--   - Full-text search uses 'simple' configuration (consider 'polish' later)
--
-- Author: Database Schema v1
-- Created: 2025-10-21
-- ============================================================================

-- ============================================================================
-- Section 1: Helper Functions
-- ============================================================================

-- Function: Automatically update updated_at timestamp on row modification
-- Used by: All main tables with updated_at column
create or replace function set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

comment on function set_updated_at() is 'Automatically sets updated_at to current timestamp on UPDATE operations';

-- Function: Enforce route tags limit (1-3 tags per route)
-- Used by: route_tags table constraint trigger
-- Note: Uses DEFERRABLE trigger to allow batch inserts within transaction
create or replace function enforce_route_tags_limit() returns trigger as $$
declare
  tag_count integer;
begin
  -- Count tags for the affected route
  select count(*) into tag_count
  from route_tags
  where route_id = new.route_id;
  
  -- Validate tag count is within allowed range (1-3)
  if tg_op in ('INSERT', 'UPDATE') then
    if tag_count < 1 then
      raise exception 'Route must have at least 1 tag (route_id: %)', new.route_id;
    elsif tag_count > 3 then
      raise exception 'Route must not have more than 3 tags (route_id: %, current: %)', new.route_id, tag_count;
    end if;
  end if;
  
  return new;
end;
$$ language plpgsql;

comment on function enforce_route_tags_limit() is 'Ensures each route has between 1 and 3 tags';

-- Function: Enforce route points limit based on route type
-- Used by: route_points table triggers
-- Business rules:
--   - AI-generated routes: max 7 points
--   - Manual routes: max 10 points
create or replace function enforce_route_points_limit() returns trigger as $$
declare
  point_count integer;
  rt_type text;
begin
  -- Get route type
  select route_type into rt_type
  from routes
  where id = new.route_id;
  
  -- Count active (non-removed) points for the route
  select count(*) into point_count
  from route_points
  where route_id = new.route_id
    and is_removed = false;
  
  -- Validate point count based on route type
  if rt_type = 'ai_generated' and point_count > 7 then
    raise exception 'AI-generated routes must have at most 7 points (route_id: %, current: %)', new.route_id, point_count;
  elsif rt_type = 'manual' and point_count > 10 then
    raise exception 'Manual routes must have at most 10 points (route_id: %, current: %)', new.route_id, point_count;
  end if;
  
  return new;
end;
$$ language plpgsql;

comment on function enforce_route_points_limit() is 'Enforces maximum point count: 7 for AI-generated, 10 for manual routes';

-- ============================================================================
-- Section 2: Core Tables Creation
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: places
-- ----------------------------------------------------------------------------
-- Purpose: Store geographic places/locations that can be added to routes
-- Notes:
--   - Supports both OSM and Wikipedia as data sources
--   - lat/lon validated within geographic bounds
--   - JSONB data field for flexible external data storage
--   - Future: PostGIS geometry column to be added
create table places (
  id bigserial primary key,
  name text not null,
  osm_id bigint null unique,
  wikipedia_id text null unique,
  address text null,
  city text null,
  country text null,
  lat double precision not null check (lat between -90 and 90),
  lon double precision not null check (lon between -180 and 180),
  data jsonb null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table places is 'Geographic places/locations that can be included in routes';
comment on column places.osm_id is 'OpenStreetMap place identifier (unique)';
comment on column places.wikipedia_id is 'Wikipedia article identifier (unique)';
comment on column places.lat is 'Latitude in decimal degrees (-90 to 90)';
comment on column places.lon is 'Longitude in decimal degrees (-180 to 180)';
comment on column places.data is 'Additional metadata from external sources (OSM, Wikipedia) stored as JSON';

-- ----------------------------------------------------------------------------
-- Table: tags
-- ----------------------------------------------------------------------------
-- Purpose: Categorization tags for routes (e.g., "historical", "nature")
-- Notes:
--   - Case-insensitive uniqueness enforced via functional index
--   - Priority field for display ordering
--   - is_active flag for soft deprecation
create table tags (
  id bigserial primary key,
  name text not null,
  description text null,
  is_active boolean not null default true,
  priority integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table tags is 'Categorization tags for routes (e.g., historical, nature, architecture)';
comment on column tags.name is 'Tag name (case-insensitive unique)';
comment on column tags.is_active is 'Whether tag is available for new routes';
comment on column tags.priority is 'Display priority (higher = more important)';

-- ----------------------------------------------------------------------------
-- Table: routes
-- ----------------------------------------------------------------------------
-- Purpose: User-created routes (collections of places in specific order)
-- Notes:
--   - Owned by Django auth_user
--   - status: 'temporary' (unsaved draft) or 'saved' (persistent)
--   - route_type: 'ai_generated' or 'manual'
--   - Caching fields for external route optimization data
-- DESTRUCTIVE WARNING: ON DELETE CASCADE will remove all related data
create table routes (
  id bigserial primary key,
  user_id bigint not null,
  name text not null,
  status text not null check (status in ('temporary', 'saved')),
  route_type text not null check (route_type in ('ai_generated', 'manual')),
  saved_at timestamptz null,
  cached_at timestamptz null,
  cache_expires_at timestamptz null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  
  constraint fk_routes_user
    foreign key (user_id)
    references auth_user(id)
    on delete cascade
);

comment on table routes is 'User-created routes containing ordered collections of places';
comment on column routes.status is 'Route persistence status: temporary (draft) or saved (persistent)';
comment on column routes.route_type is 'Creation method: ai_generated or manual';
comment on column routes.saved_at is 'Timestamp when route was first saved (null for temporary)';
comment on column routes.cached_at is 'Timestamp of last route optimization cache update';
comment on column routes.cache_expires_at is 'Expiration time for cached optimization data';

-- ----------------------------------------------------------------------------
-- Table: route_points
-- ----------------------------------------------------------------------------
-- Purpose: Many-to-many relationship between routes and places with ordering
-- Notes:
--   - position: base ordering of points in route
--   - optimized_position: ordering after route optimization (null if not optimized)
--   - is_removed: soft delete flag for user-removed points
--   - source: tracks whether point was AI-suggested or manually added
-- DESTRUCTIVE WARNING: ON DELETE CASCADE from parent route or place
create table route_points (
  id bigserial primary key,
  route_id bigint not null,
  place_id bigint not null,
  source text not null check (source in ('ai_generated', 'manual')),
  position integer not null,
  optimized_position integer null,
  is_removed boolean not null default false,
  added_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  
  constraint fk_route_points_route
    foreign key (route_id)
    references routes(id)
    on delete cascade,
  
  constraint fk_route_points_place
    foreign key (place_id)
    references places(id)
    on delete cascade
);

comment on table route_points is 'Ordered collection of places within a route';
comment on column route_points.position is 'Base position/order in route sequence';
comment on column route_points.optimized_position is 'Position after route optimization (null if not optimized)';
comment on column route_points.is_removed is 'Soft delete flag - true if user removed this point';
comment on column route_points.source is 'Origin of point: ai_generated or manual';
comment on column route_points.added_at is 'Timestamp when point was added to route';

-- ----------------------------------------------------------------------------
-- Table: place_descriptions
-- ----------------------------------------------------------------------------
-- Purpose: AI-generated or user-edited descriptions for places in routes
-- Notes:
--   - 1:1 relationship with route_points (enforced by unique constraint)
--   - Content length validated: 2500-5000 characters
--   - Supports multiple languages (default: Polish)
-- DESTRUCTIVE WARNING: ON DELETE CASCADE from parent route_point
create table place_descriptions (
  id bigserial primary key,
  route_point_id bigint not null unique,
  language_code varchar(8) not null default 'pl',
  content text not null check (char_length(content) between 2500 and 5000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  
  constraint fk_place_descriptions_route_point
    foreign key (route_point_id)
    references route_points(id)
    on delete cascade
);

comment on table place_descriptions is 'AI-generated or user-edited descriptions for places in routes';
comment on column place_descriptions.route_point_id is 'Related route point (1:1 relationship)';
comment on column place_descriptions.language_code is 'ISO language code (e.g., pl, en, de)';
comment on column place_descriptions.content is 'Description text (2500-5000 characters)';
comment on column place_descriptions.created_by_ai is 'Whether description was AI-generated or manually written';

-- ----------------------------------------------------------------------------
-- Table: route_tags
-- ----------------------------------------------------------------------------
-- Purpose: Many-to-many relationship between routes and tags
-- Notes:
--   - Composite primary key (route_id, tag_id)
--   - Each route must have 1-3 tags (enforced by trigger)
--   - ON DELETE RESTRICT for tags prevents deletion of used tags
-- DESTRUCTIVE WARNING: ON DELETE CASCADE from route, RESTRICT from tag
create table route_tags (
  route_id bigint not null,
  tag_id bigint not null,
  created_at timestamptz not null default now(),
  
  primary key (route_id, tag_id),
  
  constraint fk_route_tags_route
    foreign key (route_id)
    references routes(id)
    on delete cascade,
  
  constraint fk_route_tags_tag
    foreign key (tag_id)
    references tags(id)
    on delete restrict
);

comment on table route_tags is 'Many-to-many relationship between routes and tags (1-3 tags per route)';

-- ----------------------------------------------------------------------------
-- Table: ratings
-- ----------------------------------------------------------------------------
-- Purpose: User ratings/votes for routes and place descriptions
-- Notes:
--   - Polymorphic design: rates either route OR place_description
--   - rating_value: +1 (upvote) or -1 (downvote)
--   - Enforces one rating per user per target (via partial unique indexes)
--   - CHECK constraint ensures rating_type matches populated FK
-- DESTRUCTIVE WARNING: ON DELETE CASCADE from all parent entities
create table ratings (
  id bigserial primary key,
  user_id bigint not null,
  rating_type text not null check (rating_type in ('place_description', 'route')),
  rating_value smallint not null check (rating_value in (-1, 1)),
  route_id bigint null,
  place_description_id bigint null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  
  constraint fk_ratings_user
    foreign key (user_id)
    references auth_user(id)
    on delete cascade,
  
  constraint fk_ratings_route
    foreign key (route_id)
    references routes(id)
    on delete cascade,
  
  constraint fk_ratings_place_description
    foreign key (place_description_id)
    references place_descriptions(id)
    on delete cascade,
  
  -- Ensure exactly one target FK is set based on rating_type
  constraint chk_ratings_target_consistency check (
    (rating_type = 'route' and route_id is not null and place_description_id is null) or
    (rating_type = 'place_description' and place_description_id is not null and route_id is null)
  )
);

comment on table ratings is 'User upvotes/downvotes for routes and place descriptions';
comment on column ratings.rating_type is 'Type of rated entity: route or place_description';
comment on column ratings.rating_value is 'Vote direction: +1 (upvote) or -1 (downvote)';
comment on column ratings.route_id is 'Target route (populated when rating_type=route)';
comment on column ratings.place_description_id is 'Target place description (populated when rating_type=place_description)';

-- ----------------------------------------------------------------------------
-- Table: ai_generation_logs
-- ----------------------------------------------------------------------------
-- Purpose: Audit log for AI route generation requests
-- Notes:
--   - Tracks model usage, token consumption, and costs
--   - Stores snapshot of generation parameters (tags, text)
--   - Useful for analytics, debugging, and cost tracking
-- DESTRUCTIVE WARNING: ON DELETE CASCADE from parent route
create table ai_generation_logs (
  id bigserial primary key,
  route_id bigint not null,
  model text not null,
  provider text null,
  prompt_hash text null,
  tags_snapshot text[] not null default '{}',
  additional_text_snapshot text null,
  points_count integer null check (points_count between 0 and 7),
  tokens_prompt integer null check (tokens_prompt >= 0),
  tokens_completion integer null check (tokens_completion >= 0),
  cost_usd numeric(10,4) null check (cost_usd >= 0),
  request_id text null,
  metadata jsonb null,
  created_at timestamptz not null default now(),
  
  constraint fk_ai_generation_logs_route
    foreign key (route_id)
    references routes(id)
    on delete cascade
);

comment on table ai_generation_logs is 'Audit log of AI route generation requests for analytics and cost tracking';
comment on column ai_generation_logs.model is 'AI model name/version used for generation';
comment on column ai_generation_logs.provider is 'AI service provider (e.g., OpenAI, Anthropic)';
comment on column ai_generation_logs.prompt_hash is 'Hash of prompt for deduplication analysis';
comment on column ai_generation_logs.tags_snapshot is 'Array of tag names used in generation prompt';
comment on column ai_generation_logs.additional_text_snapshot is 'User-provided additional text for generation';
comment on column ai_generation_logs.points_count is 'Number of points generated (0-7 for AI routes)';
comment on column ai_generation_logs.tokens_prompt is 'Token count in prompt';
comment on column ai_generation_logs.tokens_completion is 'Token count in completion';
comment on column ai_generation_logs.cost_usd is 'Estimated cost in USD';
comment on column ai_generation_logs.request_id is 'External request/trace ID from AI provider';
comment on column ai_generation_logs.metadata is 'Additional metadata as JSON';

-- ============================================================================
-- Section 3: Indexes for Performance
-- ============================================================================

-- Routes indexes
-- Multi-column index for common query pattern: user's routes filtered by status, ordered by creation
create index routes_idx_user_status_created on routes (user_id, status, created_at desc);
comment on index routes_idx_user_status_created is 'Optimizes queries for user routes filtered by status and ordered by creation date';

-- Index for filtering routes by type
create index routes_idx_route_type on routes (route_type);
comment on index routes_idx_route_type is 'Optimizes filtering routes by creation method (AI vs manual)';

-- Route points indexes
-- Composite index for retrieving ordered points within a route
create index route_points_idx_route_position on route_points (route_id, position);
comment on index route_points_idx_route_position is 'Optimizes retrieving points in correct order for a route';

-- Index for filtering removed/active points
create index route_points_idx_route_removed on route_points (route_id, is_removed);
comment on index route_points_idx_route_removed is 'Optimizes filtering active vs removed points in a route';

-- Partial unique index: ensures unique position among active points in a route
create unique index route_points_uniq_position_active
  on route_points (route_id, position)
  where is_removed = false;
comment on index route_points_uniq_position_active is 'Ensures unique position values among active (non-removed) points in each route';

-- Places indexes
-- Spatial index for geographic queries (distance, bounding box)
create index places_idx_lat_lon on places (lat, lon);
comment on index places_idx_lat_lon is 'Optimizes geographic queries by coordinates (will be replaced by PostGIS GIST index)';

-- Full-text search index for place names and addresses
create index places_idx_name_address_fts
  on places
  using gin (to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(address, '')));
comment on index places_idx_name_address_fts is 'Full-text search index for place names and addresses (consider polish dictionary later)';

-- Tags indexes
-- Case-insensitive unique index on tag names
create unique index tags_uniq_lower_name on tags (lower(name));
comment on index tags_uniq_lower_name is 'Enforces case-insensitive uniqueness of tag names';

-- Route tags indexes
-- Index for reverse lookup: find routes with specific tag
create index route_tags_idx_tag on route_tags (tag_id);
comment on index route_tags_idx_tag is 'Optimizes finding all routes associated with a specific tag';

-- Place descriptions indexes
-- Full-text search index for description content
create index place_descriptions_idx_fts
  on place_descriptions
  using gin (to_tsvector('simple', content));
comment on index place_descriptions_idx_fts is 'Full-text search index for place description content';

-- Ratings indexes
-- Index for finding all ratings by a user
create index ratings_idx_user on ratings (user_id);
comment on index ratings_idx_user is 'Optimizes finding all ratings by a specific user';

-- Partial unique indexes: one rating per user per target
create unique index ratings_uniq_user_route
  on ratings (user_id, route_id)
  where rating_type = 'route';
comment on index ratings_uniq_user_route is 'Ensures each user can rate a route only once';

create unique index ratings_uniq_user_place_description
  on ratings (user_id, place_description_id)
  where rating_type = 'place_description';
comment on index ratings_uniq_user_place_description is 'Ensures each user can rate a place description only once';

-- AI generation logs indexes
-- Index for finding logs by route, ordered by creation
create index ai_generation_logs_idx_route_created
  on ai_generation_logs (route_id, created_at desc);
comment on index ai_generation_logs_idx_route_created is 'Optimizes retrieving generation history for a route';

-- ============================================================================
-- Section 4: Audit Triggers (updated_at)
-- ============================================================================

-- Apply updated_at trigger to all main tables
-- These triggers automatically update the updated_at timestamp on row modification

create trigger set_updated_at_routes
  before update on routes
  for each row
  execute function set_updated_at();

create trigger set_updated_at_places
  before update on places
  for each row
  execute function set_updated_at();

create trigger set_updated_at_route_points
  before update on route_points
  for each row
  execute function set_updated_at();

create trigger set_updated_at_place_descriptions
  before update on place_descriptions
  for each row
  execute function set_updated_at();

create trigger set_updated_at_tags
  before update on tags
  for each row
  execute function set_updated_at();

create trigger set_updated_at_ratings
  before update on ratings
  for each row
  execute function set_updated_at();

-- ============================================================================
-- Section 5: Business Logic Constraint Triggers
-- ============================================================================

-- Trigger: Enforce route tags limit (1-3 tags per route)
-- DEFERRABLE INITIALLY DEFERRED allows batch tag inserts within transaction
create constraint trigger route_tags_limit
  after insert or delete or update on route_tags
  deferrable initially deferred
  for each row
  execute function enforce_route_tags_limit();

comment on trigger route_tags_limit on route_tags is 'Enforces 1-3 tags per route (deferred to allow batch operations)';

-- Triggers: Enforce route points limit based on route type
-- AI routes: max 7 points, Manual routes: max 10 points

create trigger route_points_limit_insert
  after insert on route_points
  for each row
  execute function enforce_route_points_limit();

comment on trigger route_points_limit_insert on route_points is 'Validates point count on insert (7 for AI, 10 for manual)';

create trigger route_points_limit_update
  after update of is_removed on route_points
  for each row
  execute function enforce_route_points_limit();

comment on trigger route_points_limit_update on route_points is 'Validates point count when is_removed flag changes';

-- ============================================================================
-- Section 6: Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on tables containing user-specific data
-- Note: Application must set session variable 'app.user_id' before queries
--       Example: SELECT set_config('app.user_id', '123', true);

alter table routes enable row level security;
alter table route_points enable row level security;
alter table place_descriptions enable row level security;
alter table ratings enable row level security;

comment on table routes is E'User-created routes containing ordered collections of places\nRLS enabled: users can only access their own routes';
comment on table route_points is E'Ordered collection of places within a route\nRLS enabled: access derived from route ownership';
comment on table place_descriptions is E'AI-generated or user-edited descriptions for places in routes\nRLS enabled: access derived from route ownership';
comment on table ratings is E'User upvotes/downvotes for routes and place descriptions\nRLS enabled: users can only see and modify their own ratings';

-- ============================================================================
-- RLS Policies: routes table
-- ============================================================================
-- Users can only access their own routes (based on user_id column)
-- Application must set 'app.user_id' session variable to current user's ID

-- Policy: SELECT - users can view their own routes
create policy routes_owner_select on routes
  for select
  using (user_id = current_setting('app.user_id', true)::bigint);

comment on policy routes_owner_select on routes is 'Users can only SELECT their own routes (via app.user_id session variable)';

-- Policy: INSERT - users can only insert routes for themselves
create policy routes_owner_insert on routes
  for insert
  with check (user_id = current_setting('app.user_id', true)::bigint);

comment on policy routes_owner_insert on routes is 'Users can only INSERT routes with their own user_id';

-- Policy: UPDATE - users can only update their own routes
create policy routes_owner_update on routes
  for update
  using (user_id = current_setting('app.user_id', true)::bigint)
  with check (user_id = current_setting('app.user_id', true)::bigint);

comment on policy routes_owner_update on routes is 'Users can only UPDATE their own routes and cannot change ownership';

-- Policy: DELETE - users can only delete their own routes
create policy routes_owner_delete on routes
  for delete
  using (user_id = current_setting('app.user_id', true)::bigint);

comment on policy routes_owner_delete on routes is 'Users can only DELETE their own routes';

-- ============================================================================
-- RLS Policies: route_points table
-- ============================================================================
-- Access to route points is derived from route ownership
-- Users can access route_points only if they own the parent route

-- Policy: ALL operations - check route ownership
create policy route_points_owner on route_points
  for all
  using (
    exists (
      select 1
      from routes r
      where r.id = route_points.route_id
        and r.user_id = current_setting('app.user_id', true)::bigint
    )
  )
  with check (
    exists (
      select 1
      from routes r
      where r.id = route_points.route_id
        and r.user_id = current_setting('app.user_id', true)::bigint
    )
  );

comment on policy route_points_owner on route_points is 'Users can access route_points only for routes they own';

-- ============================================================================
-- RLS Policies: place_descriptions table
-- ============================================================================
-- Access to place descriptions is derived from route ownership via route_points
-- Users can access place_descriptions only if they own the route containing the point

-- Policy: ALL operations - check route ownership through route_points
create policy place_descriptions_owner on place_descriptions
  for all
  using (
    exists (
      select 1
      from route_points rp
      join routes r on r.id = rp.route_id
      where rp.id = place_descriptions.route_point_id
        and r.user_id = current_setting('app.user_id', true)::bigint
    )
  )
  with check (
    exists (
      select 1
      from route_points rp
      join routes r on r.id = rp.route_id
      where rp.id = place_descriptions.route_point_id
        and r.user_id = current_setting('app.user_id', true)::bigint
    )
  );

comment on policy place_descriptions_owner on place_descriptions is 'Users can access place_descriptions only for routes they own (via route_points)';

-- ============================================================================
-- RLS Policies: ratings table
-- ============================================================================
-- Users can only see and modify their own ratings
-- Users cannot see or modify ratings created by other users

-- Policy: SELECT - users can view their own ratings
create policy ratings_owner_select on ratings
  for select
  using (user_id = current_setting('app.user_id', true)::bigint);

comment on policy ratings_owner_select on ratings is 'Users can only SELECT their own ratings';

-- Policy: INSERT - users can only create ratings for themselves
create policy ratings_owner_insert on ratings
  for insert
  with check (user_id = current_setting('app.user_id', true)::bigint);

comment on policy ratings_owner_insert on ratings is 'Users can only INSERT ratings with their own user_id';

-- Policy: UPDATE - users can only update their own ratings
create policy ratings_owner_update on ratings
  for update
  using (user_id = current_setting('app.user_id', true)::bigint)
  with check (user_id = current_setting('app.user_id', true)::bigint);

comment on policy ratings_owner_update on ratings is 'Users can only UPDATE their own ratings and cannot change ownership';

-- Policy: DELETE - users can only delete their own ratings
create policy ratings_owner_delete on ratings
  for delete
  using (user_id = current_setting('app.user_id', true)::bigint);

comment on policy ratings_owner_delete on ratings is 'Users can only DELETE their own ratings';

-- ============================================================================
-- End of Migration
-- ============================================================================

-- Migration completed successfully
-- Summary:
--   - 8 tables created (places, tags, routes, route_points, place_descriptions, route_tags, ratings, ai_generation_logs)
--   - 16 indexes created (including partial unique, full-text search, and composite indexes)
--   - 4 tables with RLS enabled (routes, route_points, place_descriptions, ratings)
--   - 13 RLS policies created (granular policies for each operation type)
--   - 8 triggers created (6 for updated_at, 2 for business constraints)
--   - 3 helper functions created (updated_at, tags limit, points limit)

