Database Implementation Plan
1. PostgreSQL Configuration
Docker Setup
Add PostgreSQL 16 service to docker-compose.yml
Create .env file with database credentials
Configure volumes for data persistence
Django Settings
Update pathie/settings.py:
Configure PostgreSQL as default database engine
Add timezone settings (UTC)
Ensure DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
2. Create Core Django App
Run python manage.py startapp core in /home/pszczod/Pathie/pathie/
Register core in INSTALLED_APPS
Create directory structure:
core/models/ (split models for readability)
core/migrations/sql/ (for SQL layer files)
3. Define Django Models (ORM Layer)
Create models in core/models/ following the schema from 09-db-plan-v1.md:

core/models/route.py
Route model with fields: user, name, status, route_type, saved_at, cached_at, cache_expires_at, timestamps
Status choices: 'temporary', 'saved'
Route type choices: 'ai_generated', 'manual'
FK to auth.User with CASCADE delete
core/models/place.py
Place model: name, osm_id, wikipedia_id, address, city, country, lat, lon, data (JSONField), timestamps
Validation for lat (-90 to 90), lon (-180 to 180)
Unique constraints on osm_id, wikipedia_id
core/models/route_point.py
RoutePoint model: route, place, source, position, optimized_position, is_removed, added_at, timestamps
Source choices: 'ai_generated', 'manual'
FKs with CASCADE delete
core/models/place_description.py
PlaceDescription model: route_point (OneToOne), language_code, content, timestamps
Content length validation (2500-5000 chars)
core/models/tag.py
Tag model: name, description, is_active, priority, timestamps
RouteTag through model for M2M with Route
core/models/rating.py
Rating model: user, rating_type, rating_value, route, place_description, timestamps
Rating type choices: 'place_description', 'route'
Rating value choices: -1, 1
CHECK constraint logic for rating_type vs target fields
core/models/ai_log.py
AIGenerationLog model: route, model, provider, prompt_hash, tags_snapshot (ArrayField), additional_text_snapshot, points_count, tokens_prompt, tokens_completion, cost_usd, request_id, metadata (JSONField), created_at
Validation for numeric constraints
core/models/__init__.py
Import and expose all models
4. Create Initial Migration
Run python manage.py makemigrations core
Review migration file to ensure all structure is captured
Do NOT apply yet (SQL layer comes next)
5. SQL Layer - Create SQL Files
Create individual SQL files in core/migrations/sql/:

0001_indexes.sql
Composite btree indexes (routes, route_points, ratings, ai_logs)
UNIQUE PARTIAL indexes (route_points position, ratings uniqueness)
Functional index for tags (lower(name))
GIN indexes for full-text search (places, place_descriptions)
0002_rls_policies.sql
Enable RLS on: routes, route_points, place_descriptions, ratings
Create policies:
routes: direct ownership (user_id match)
route_points: derived via routes
place_descriptions: derived via route_points + routes
ratings: direct ownership
0003_triggers.sql
set_updated_at() function for automatic timestamp updates
Apply trigger to all tables with updated_at field
enforce_route_tags_limit() DEFERRABLE constraint trigger (1-3 tags)
enforce_route_points_limit() trigger (AI ≤7, manual ≤10)
0004_check_constraints.sql
Multi-column CHECK on ratings (rating_type vs target field consistency)
Additional business logic constraints if not expressible in ORM
6. Create SQL Migration
Create custom migration core/migrations/0002_sql_layer.py
Use migrations.RunSQL() to execute each SQL file in order
Provide reverse_sql for down migration (DROP policies, triggers, indexes)
7. RLS Middleware
core/middleware.py
Create PostgreSQLRLSMiddleware class
Set app.user_id config for authenticated users
Handle connection cursor properly
Update Settings
Add middleware to MIDDLEWARE list in settings.py (after AuthenticationMiddleware)
8. Database Initialization
Run python manage.py migrate
Verify all tables, indexes, policies, and triggers are created
Test RLS with sample user and queries
9. Admin Configuration (Optional)
Create core/admin.py registering key models
Useful for initial data entry and testing
---

Key Files to Create/Modify
New files:

core/models/*.py (8 model files)
core/migrations/sql/*.sql (4 SQL files)
core/middleware.py
.env (database credentials)
Modified files:

docker-compose.yml (add postgres service)
pathie/settings.py (database config, middleware, installed apps)
Implementation Notes
Follow db-rules.mdc: ORM for structure, SQL for logic/security
All SQL files must be idempotent (CREATE OR REPLACE, DROP IF EXISTS)
Test RLS policies work correctly by setting app.user_id in queries
Use type annotations in all Python code
Keep migrations atomic and well-documented