"""
SQL Layer Migration - Indexes, RLS, Triggers, and Constraints
Applies PostgreSQL-specific features following hybrid architecture.
"""
from pathlib import Path

from django.db import migrations


def load_sql(filename: str) -> str:
    """Load SQL file from migrations/sql/ directory."""
    sql_dir = Path(__file__).parent / 'sql'
    sql_file = sql_dir / filename
    return sql_file.read_text()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # ====================================================================
        # INDEXES (UNIQUE PARTIAL, FUNCTIONAL, GIN)
        # ====================================================================
        migrations.RunSQL(
            sql=load_sql('0001_indexes.sql'),
            reverse_sql="""
                DROP INDEX IF EXISTS route_points_uniq_position_active;
                DROP INDEX IF EXISTS ratings_uniq_user_route;
                DROP INDEX IF EXISTS ratings_uniq_user_place_desc;
                DROP INDEX IF EXISTS tags_uniq_lower_name;
                DROP INDEX IF EXISTS places_idx_name_address_fts;
                DROP INDEX IF EXISTS place_descriptions_idx_fts;
            """,
        ),
        
        # ====================================================================
        # ROW LEVEL SECURITY POLICIES
        # ====================================================================
        migrations.RunSQL(
            sql=load_sql('0002_rls_policies.sql'),
            reverse_sql="""
                -- Disable RLS
                ALTER TABLE routes DISABLE ROW LEVEL SECURITY;
                ALTER TABLE route_points DISABLE ROW LEVEL SECURITY;
                ALTER TABLE place_descriptions DISABLE ROW LEVEL SECURITY;
                ALTER TABLE ratings DISABLE ROW LEVEL SECURITY;
                
                -- Drop policies
                DROP POLICY IF EXISTS routes_owner_select ON routes;
                DROP POLICY IF EXISTS routes_owner_insert ON routes;
                DROP POLICY IF EXISTS routes_owner_update ON routes;
                DROP POLICY IF EXISTS routes_owner_delete ON routes;
                DROP POLICY IF EXISTS route_points_owner ON route_points;
                DROP POLICY IF EXISTS place_descriptions_owner ON place_descriptions;
                DROP POLICY IF EXISTS ratings_owner_select ON ratings;
                DROP POLICY IF EXISTS ratings_owner_modify ON ratings;
            """,
        ),
        
        # ====================================================================
        # TRIGGERS AND FUNCTIONS
        # ====================================================================
        migrations.RunSQL(
            sql=load_sql('0003_triggers.sql'),
            reverse_sql="""
                -- Drop triggers
                DROP TRIGGER IF EXISTS set_updated_at_routes ON routes;
                DROP TRIGGER IF EXISTS set_updated_at_places ON places;
                DROP TRIGGER IF EXISTS set_updated_at_route_points ON route_points;
                DROP TRIGGER IF EXISTS set_updated_at_place_descriptions ON place_descriptions;
                DROP TRIGGER IF EXISTS set_updated_at_tags ON tags;
                DROP TRIGGER IF EXISTS set_updated_at_ratings ON ratings;
                DROP TRIGGER IF EXISTS route_tags_limit ON route_tags;
                DROP TRIGGER IF EXISTS route_points_limit_insert ON route_points;
                DROP TRIGGER IF EXISTS route_points_limit_update ON route_points;
                
                -- Drop functions
                DROP FUNCTION IF EXISTS set_updated_at();
                DROP FUNCTION IF EXISTS enforce_route_tags_limit();
                DROP FUNCTION IF EXISTS enforce_route_points_limit();
            """,
        ),
        
        # ====================================================================
        # CHECK CONSTRAINTS
        # ====================================================================
        migrations.RunSQL(
            sql=load_sql('0004_check_constraints.sql'),
            reverse_sql="""
                ALTER TABLE ratings DROP CONSTRAINT IF EXISTS chk_rating_type_consistency;
                ALTER TABLE ratings DROP CONSTRAINT IF EXISTS chk_rating_value_valid;
                ALTER TABLE routes DROP CONSTRAINT IF EXISTS chk_status_valid;
                ALTER TABLE routes DROP CONSTRAINT IF EXISTS chk_route_type_valid;
                ALTER TABLE places DROP CONSTRAINT IF EXISTS chk_lat_range;
                ALTER TABLE places DROP CONSTRAINT IF EXISTS chk_lon_range;
                ALTER TABLE place_descriptions DROP CONSTRAINT IF EXISTS chk_content_length;
                ALTER TABLE ai_generation_logs DROP CONSTRAINT IF EXISTS chk_points_count_range;
                ALTER TABLE ai_generation_logs DROP CONSTRAINT IF EXISTS chk_tokens_positive;
                ALTER TABLE ai_generation_logs DROP CONSTRAINT IF EXISTS chk_cost_positive;
                ALTER TABLE route_points DROP CONSTRAINT IF EXISTS chk_source_valid;
            """,
        ),
    ]

