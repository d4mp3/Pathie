-- Additional indexes beyond what Django ORM creates
-- Following hybrid architecture: specialized indexes for PostgreSQL

-- ============================================================================
-- UNIQUE PARTIAL INDEXES (for conditional uniqueness)
-- ============================================================================

-- Ensure unique position for active (non-removed) route points
CREATE UNIQUE INDEX IF NOT EXISTS route_points_uniq_position_active
ON route_points (route_id, position)
WHERE is_removed = false;

COMMENT ON INDEX route_points_uniq_position_active IS 
'Enforces unique position per route for active (non-removed) points only';

-- Ensure user can only rate each route once
CREATE UNIQUE INDEX IF NOT EXISTS ratings_uniq_user_route
ON ratings (user_id, route_id)
WHERE rating_type = 'route';

COMMENT ON INDEX ratings_uniq_user_route IS 
'Ensures one rating per user per route';

-- Ensure user can only rate each place description once
CREATE UNIQUE INDEX IF NOT EXISTS ratings_uniq_user_place_desc
ON ratings (user_id, place_description_id)
WHERE rating_type = 'place_description';

COMMENT ON INDEX ratings_uniq_user_place_desc IS 
'Ensures one rating per user per place description';

-- ============================================================================
-- FUNCTIONAL INDEXES (case-insensitive, computed values)
-- ============================================================================

-- Case-insensitive unique tag names
CREATE UNIQUE INDEX IF NOT EXISTS tags_uniq_lower_name
ON tags (lower(name));

COMMENT ON INDEX tags_uniq_lower_name IS 
'Enforces case-insensitive unique tag names';

-- ============================================================================
-- GIN INDEXES (full-text search)
-- ============================================================================

-- Full-text search on place names and addresses
CREATE INDEX IF NOT EXISTS places_idx_name_address_fts
ON places USING GIN (
    to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(address, ''))
);

COMMENT ON INDEX places_idx_name_address_fts IS 
'Full-text search index for place names and addresses';

-- Full-text search on place descriptions
CREATE INDEX IF NOT EXISTS place_descriptions_idx_fts
ON place_descriptions USING GIN (
    to_tsvector('simple', content)
);

COMMENT ON INDEX place_descriptions_idx_fts IS 
'Full-text search index for place description content';

