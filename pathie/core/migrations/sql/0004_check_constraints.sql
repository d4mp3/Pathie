-- CHECK Constraints for Data Integrity
-- Complex business rules that can't be fully expressed in Django ORM

-- ============================================================================
-- RATINGS: Ensure rating_type matches target field
-- ============================================================================

-- Ensure consistency between rating_type and target fields
-- - When rating_type = 'route': route_id must be NOT NULL, place_description_id must be NULL
-- - When rating_type = 'place_description': place_description_id must be NOT NULL, route_id must be NULL

ALTER TABLE ratings DROP CONSTRAINT IF EXISTS chk_rating_type_consistency;

ALTER TABLE ratings ADD CONSTRAINT chk_rating_type_consistency CHECK (
    (rating_type = 'route' AND route_id IS NOT NULL AND place_description_id IS NULL)
    OR
    (rating_type = 'place_description' AND place_description_id IS NOT NULL AND route_id IS NULL)
);

COMMENT ON CONSTRAINT chk_rating_type_consistency ON ratings IS
'Ensures rating_type matches the target field: route XOR place_description';

-- ============================================================================
-- ROUTES: Ensure status and route_type are valid
-- ============================================================================

ALTER TABLE routes DROP CONSTRAINT IF EXISTS chk_status_valid;
ALTER TABLE routes ADD CONSTRAINT chk_status_valid CHECK (
    status IN ('temporary', 'saved')
);

COMMENT ON CONSTRAINT chk_status_valid ON routes IS
'Ensures route status is either temporary or saved';

ALTER TABLE routes DROP CONSTRAINT IF EXISTS chk_route_type_valid;
ALTER TABLE routes ADD CONSTRAINT chk_route_type_valid CHECK (
    route_type IN ('ai_generated', 'manual')
);

COMMENT ON CONSTRAINT chk_route_type_valid ON routes IS
'Ensures route type is either ai_generated or manual';

-- ============================================================================
-- PLACES: Ensure lat/lon are within valid ranges
-- ============================================================================

ALTER TABLE places DROP CONSTRAINT IF EXISTS chk_lat_range;
ALTER TABLE places ADD CONSTRAINT chk_lat_range CHECK (
    lat BETWEEN -90 AND 90
);

COMMENT ON CONSTRAINT chk_lat_range ON places IS
'Ensures latitude is between -90 and 90 degrees';

ALTER TABLE places DROP CONSTRAINT IF EXISTS chk_lon_range;
ALTER TABLE places ADD CONSTRAINT chk_lon_range CHECK (
    lon BETWEEN -180 AND 180
);

COMMENT ON CONSTRAINT chk_lon_range ON places IS
'Ensures longitude is between -180 and 180 degrees';

-- ============================================================================
-- PLACE_DESCRIPTIONS: Ensure content length is within bounds
-- ============================================================================

ALTER TABLE place_descriptions DROP CONSTRAINT IF EXISTS chk_content_length;
ALTER TABLE place_descriptions ADD CONSTRAINT chk_content_length CHECK (
    char_length(content) BETWEEN 2500 AND 5000
);

COMMENT ON CONSTRAINT chk_content_length ON place_descriptions IS
'Ensures description content is between 2500 and 5000 characters';

-- ============================================================================
-- AI_GENERATION_LOGS: Ensure numeric values are valid
-- ============================================================================

ALTER TABLE ai_generation_logs DROP CONSTRAINT IF EXISTS chk_points_count_range;
ALTER TABLE ai_generation_logs ADD CONSTRAINT chk_points_count_range CHECK (
    points_count IS NULL OR (points_count BETWEEN 0 AND 7)
);

COMMENT ON CONSTRAINT chk_points_count_range ON ai_generation_logs IS
'Ensures points_count is between 0 and 7 for AI-generated routes';

ALTER TABLE ai_generation_logs DROP CONSTRAINT IF EXISTS chk_tokens_positive;
ALTER TABLE ai_generation_logs ADD CONSTRAINT chk_tokens_positive CHECK (
    (tokens_prompt IS NULL OR tokens_prompt >= 0)
    AND
    (tokens_completion IS NULL OR tokens_completion >= 0)
);

COMMENT ON CONSTRAINT chk_tokens_positive ON ai_generation_logs IS
'Ensures token counts are non-negative';

ALTER TABLE ai_generation_logs DROP CONSTRAINT IF EXISTS chk_cost_positive;
ALTER TABLE ai_generation_logs ADD CONSTRAINT chk_cost_positive CHECK (
    cost_usd IS NULL OR cost_usd >= 0
);

COMMENT ON CONSTRAINT chk_cost_positive ON ai_generation_logs IS
'Ensures cost is non-negative';

-- ============================================================================
-- RATINGS: Ensure rating_value is valid
-- ============================================================================

ALTER TABLE ratings DROP CONSTRAINT IF EXISTS chk_rating_value_valid;
ALTER TABLE ratings ADD CONSTRAINT chk_rating_value_valid CHECK (
    rating_value IN (-1, 1)
);

COMMENT ON CONSTRAINT chk_rating_value_valid ON ratings IS
'Ensures rating value is either -1 (downvote) or 1 (upvote)';

-- ============================================================================
-- ROUTE_POINTS: Ensure source is valid
-- ============================================================================

ALTER TABLE route_points DROP CONSTRAINT IF EXISTS chk_source_valid;
ALTER TABLE route_points ADD CONSTRAINT chk_source_valid CHECK (
    source IN ('ai_generated', 'manual')
);

COMMENT ON CONSTRAINT chk_source_valid ON route_points IS
'Ensures route point source is either ai_generated or manual';

