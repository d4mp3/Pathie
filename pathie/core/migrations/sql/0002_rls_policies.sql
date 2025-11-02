-- Row Level Security (RLS) Policies
-- Implements per-user data isolation using app.user_id session variable

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE route_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE place_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ROUTES: Direct ownership by user_id
-- ============================================================================

-- SELECT policy for routes
DROP POLICY IF EXISTS routes_owner_select ON routes;
CREATE POLICY routes_owner_select ON routes
    FOR SELECT
    USING (user_id = current_setting('app.user_id', true)::bigint);

COMMENT ON POLICY routes_owner_select ON routes IS
'User can only SELECT their own routes';

-- INSERT policy for routes
DROP POLICY IF EXISTS routes_owner_insert ON routes;
CREATE POLICY routes_owner_insert ON routes
    FOR INSERT
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);

COMMENT ON POLICY routes_owner_insert ON routes IS
'User can only INSERT routes owned by them';

-- UPDATE policy for routes
DROP POLICY IF EXISTS routes_owner_update ON routes;
CREATE POLICY routes_owner_update ON routes
    FOR UPDATE
    USING (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);

COMMENT ON POLICY routes_owner_update ON routes IS
'User can only UPDATE their own routes';

-- DELETE policy for routes
DROP POLICY IF EXISTS routes_owner_delete ON routes;
CREATE POLICY routes_owner_delete ON routes
    FOR DELETE
    USING (user_id = current_setting('app.user_id', true)::bigint);

COMMENT ON POLICY routes_owner_delete ON routes IS
'User can only DELETE their own routes';

-- ============================================================================
-- ROUTE_POINTS: Derived ownership through routes table
-- ============================================================================

DROP POLICY IF EXISTS route_points_owner ON route_points;
CREATE POLICY route_points_owner ON route_points
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM routes r
            WHERE r.id = route_points.route_id
              AND r.user_id = current_setting('app.user_id', true)::bigint
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1
            FROM routes r
            WHERE r.id = route_points.route_id
              AND r.user_id = current_setting('app.user_id', true)::bigint
        )
    );

COMMENT ON POLICY route_points_owner ON route_points IS
'User can access route_points only if they own the parent route';

-- ============================================================================
-- PLACE_DESCRIPTIONS: Derived ownership through route_points → routes
-- ============================================================================

DROP POLICY IF EXISTS place_descriptions_owner ON place_descriptions;
CREATE POLICY place_descriptions_owner ON place_descriptions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM route_points rp
            INNER JOIN routes r ON r.id = rp.route_id
            WHERE rp.id = place_descriptions.route_point_id
              AND r.user_id = current_setting('app.user_id', true)::bigint
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1
            FROM route_points rp
            INNER JOIN routes r ON r.id = rp.route_id
            WHERE rp.id = place_descriptions.route_point_id
              AND r.user_id = current_setting('app.user_id', true)::bigint
        )
    );

COMMENT ON POLICY place_descriptions_owner ON place_descriptions IS
'User can access place_descriptions only if they own the route containing the route_point';

-- ============================================================================
-- RATINGS: Direct ownership by user_id
-- ============================================================================

-- SELECT policy for ratings
DROP POLICY IF EXISTS ratings_owner_select ON ratings;
CREATE POLICY ratings_owner_select ON ratings
    FOR SELECT
    USING (user_id = current_setting('app.user_id', true)::bigint);

COMMENT ON POLICY ratings_owner_select ON ratings IS
'User can only SELECT their own ratings';

-- ALL operations policy for ratings
DROP POLICY IF EXISTS ratings_owner_modify ON ratings;
CREATE POLICY ratings_owner_modify ON ratings
    FOR ALL
    USING (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);

COMMENT ON POLICY ratings_owner_modify ON ratings IS
'User can only INSERT/UPDATE/DELETE their own ratings';

-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- Tables NOT protected by RLS:
-- - places: Shared resource, no user ownership
-- - tags: Global taxonomy
-- - route_tags: Protected by CASCADE from routes
-- - ai_generation_logs: Protected by CASCADE from routes
--
-- RLS context is set by middleware via:
--   SELECT set_config('app.user_id', '<user_id>', true);

