-- Triggers and Functions for Business Logic
-- Implements automatic updates and constraint enforcement

-- ============================================================================
-- AUTOMATIC UPDATED_AT TIMESTAMP
-- ============================================================================

-- Reusable function to update updated_at column
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_updated_at() IS
'Automatically sets updated_at to current timestamp on UPDATE';

-- Apply to all tables with updated_at column
DROP TRIGGER IF EXISTS set_updated_at_routes ON routes;
CREATE TRIGGER set_updated_at_routes
    BEFORE UPDATE ON routes
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_places ON places;
CREATE TRIGGER set_updated_at_places
    BEFORE UPDATE ON places
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_route_points ON route_points;
CREATE TRIGGER set_updated_at_route_points
    BEFORE UPDATE ON route_points
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_place_descriptions ON place_descriptions;
CREATE TRIGGER set_updated_at_place_descriptions
    BEFORE UPDATE ON place_descriptions
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_tags ON tags;
CREATE TRIGGER set_updated_at_tags
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_ratings ON ratings;
CREATE TRIGGER set_updated_at_ratings
    BEFORE UPDATE ON ratings
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- ROUTE TAGS LIMIT (1-3 tags per route)
-- ============================================================================

CREATE OR REPLACE FUNCTION enforce_route_tags_limit()
RETURNS TRIGGER AS $$
DECLARE
    tag_count INT;
BEGIN
    -- Count tags for the route (use NEW for INSERT/UPDATE, OLD for DELETE)
    IF TG_OP = 'DELETE' THEN
        SELECT COUNT(*) INTO tag_count
        FROM route_tags
        WHERE route_id = OLD.route_id;
    ELSE
        SELECT COUNT(*) INTO tag_count
        FROM route_tags
        WHERE route_id = NEW.route_id;
    END IF;
    
    -- Check constraints at end of transaction
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        IF tag_count < 1 THEN
            RAISE EXCEPTION 'Route must have at least 1 tag';
        ELSIF tag_count > 3 THEN
            RAISE EXCEPTION 'Route must not have more than 3 tags';
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        -- After delete, check remaining count
        IF tag_count < 1 THEN
            RAISE EXCEPTION 'Cannot delete tag: Route must have at least 1 tag';
        END IF;
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION enforce_route_tags_limit() IS
'Ensures each route has between 1 and 3 tags';

DROP TRIGGER IF EXISTS route_tags_limit ON route_tags;
CREATE CONSTRAINT TRIGGER route_tags_limit
    AFTER INSERT OR DELETE OR UPDATE ON route_tags
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION enforce_route_tags_limit();

-- ============================================================================
-- ROUTE POINTS LIMIT (AI ≤7, manual ≤10)
-- ============================================================================

CREATE OR REPLACE FUNCTION enforce_route_points_limit()
RETURNS TRIGGER AS $$
DECLARE
    points_count INT;
    r_type TEXT;
BEGIN
    -- Get route type
    SELECT route_type INTO r_type
    FROM routes
    WHERE id = NEW.route_id;
    
    -- Count active (non-removed) points for this route
    SELECT COUNT(*) INTO points_count
    FROM route_points
    WHERE route_id = NEW.route_id
      AND is_removed = false;
    
    -- Check limits based on route type
    IF r_type = 'ai_generated' AND points_count > 7 THEN
        RAISE EXCEPTION 'AI-generated routes must have at most 7 points (current: %)', points_count;
    ELSIF r_type = 'manual' AND points_count > 10 THEN
        RAISE EXCEPTION 'Manual routes must have at most 10 points (current: %)', points_count;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION enforce_route_points_limit() IS
'Enforces point limits: AI routes ≤7 points, manual routes ≤10 points';

-- Trigger on INSERT
DROP TRIGGER IF EXISTS route_points_limit_insert ON route_points;
CREATE TRIGGER route_points_limit_insert
    AFTER INSERT ON route_points
    FOR EACH ROW
    WHEN (NEW.is_removed = false)
    EXECUTE FUNCTION enforce_route_points_limit();

-- Trigger on UPDATE of is_removed
DROP TRIGGER IF EXISTS route_points_limit_update ON route_points;
CREATE TRIGGER route_points_limit_update
    AFTER UPDATE OF is_removed ON route_points
    FOR EACH ROW
    WHEN (NEW.is_removed = false)
    EXECUTE FUNCTION enforce_route_points_limit();

