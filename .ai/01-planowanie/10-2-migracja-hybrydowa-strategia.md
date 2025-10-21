# PROMPT: Django + PostgreSQL Hybrid Schema Implementation Strategy

## Context
You are implementing a Django application schema that requires advanced PostgreSQL features (Row-Level Security, triggers, custom functions) which cannot be expressed natively in Django ORM `models.py`. The schema is defined in <schema> @schema.sql </schema>.

## Core Principle: 80/20 Hybrid Approach
- **80%** of schema (tables, columns, FK relationships, basic indexes) → Define in `models.py` (Django ORM)
- **20%** of advanced features (RLS policies, triggers, complex constraints) → Implement via `migrations.RunPython()` with raw SQL

## Implementation Strategy

### Phase 1: Analyze SQL Schema and Create Division Plan

**Before writing any code**, analyze the SQL file and create a mental map:

1. **Extract table structures** → These become Django models in `models.py`
2. **Identify basic indexes** → Use `Meta.indexes` in models
3. **Identify foreign keys and relationships** → Use Django's `ForeignKey`, `ManyToManyField`
4. **Flag advanced features** that require raw SQL:
   - RLS policies (`CREATE POLICY`, `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`)
   - Triggers and PL/pgSQL functions
   - Complex CHECK constraints with subqueries
   - Partial/conditional unique indexes
   - Full-text search indexes (GIN)
   - Custom database functions

### Phase 2: Create Django Models (`models.py`)

**Location**: Create models in appropriate Django apps under `pathie/apps/*/models.py`

**Mapping rules**:
- SQL `bigserial` → Django `models.BigAutoField` (or use default `id`)
- SQL `text` → Django `models.TextField()`
- SQL `varchar(N)` → Django `models.CharField(max_length=N)`
- SQL `timestamptz` with `default now()` → Django `models.DateTimeField(auto_now_add=True)`
- SQL `timestamptz` → Django `models.DateTimeField()`
- SQL `boolean` → Django `models.BooleanField()`
- SQL `jsonb` → Django `models.JSONField()`
- SQL `double precision` → Django `models.FloatField()`
- SQL `CHECK (column in ('val1', 'val2'))` → Django `choices` parameter
- SQL `unique` constraint → Django `unique=True`
- SQL basic index → Django `db_index=True` or `Meta.indexes`

**Important**: 
- Use `db_table` in `Meta` to match SQL table names exactly
- Use `db_column` if Python naming conventions differ from SQL
- Always add docstrings documenting which migrations contain advanced SQL features

**Example model structure**:
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Route(models.Model):
    """
    User-created route containing ordered collection of places.
    
    SECURITY: This table has Row-Level Security (RLS) enabled.
    RLS policies are defined in migration: routes.0001_initial
    Session variable 'app.user_id' must be set before queries.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='routes',
        db_column='user_id'
    )
    name = models.TextField()
    
    STATUS_CHOICES = [
        ('temporary', 'Temporary'),
        ('saved', 'Saved'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    ROUTE_TYPE_CHOICES = [
        ('ai_generated', 'AI Generated'),
        ('manual', 'Manual'),
    ]
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPE_CHOICES)
    
    saved_at = models.DateTimeField(null=True, blank=True)
    cached_at = models.DateTimeField(null=True, blank=True)
    cache_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'routes'
        indexes = [
            models.Index(
                fields=['user', 'status', '-created_at'], 
                name='routes_idx_user_status_created'
            ),
            models.Index(
                fields=['route_type'], 
                name='routes_idx_route_type'
            ),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.user.username})"
```

### Phase 3: Create Core SQL Module for Reusability

**Location**: Create `pathie/apps/core/sql/` directory

**Structure**:
```
pathie/apps/core/
├── __init__.py
└── sql/
    ├── __init__.py
    ├── functions.py      # PL/pgSQL functions (set_updated_at, etc.)
    ├── triggers.py       # Trigger creation/removal functions
    ├── rls_policies.py   # RLS policy application functions
    ├── constraints.py    # Custom CHECK constraints
    └── indexes.py        # Advanced indexes (GIN, partial, etc.)
```

**Pattern for each module**:
```python
# pathie/apps/core/sql/functions.py
def create_set_updated_at_function(schema_editor):
    """Create set_updated_at() trigger function for auto-updating timestamps."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE OR REPLACE FUNCTION set_updated_at() 
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

def drop_set_updated_at_function(schema_editor):
    """Remove set_updated_at() function (for rollback)."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP FUNCTION IF EXISTS set_updated_at() CASCADE;")
```

```python
# pathie/apps/core/sql/rls_policies.py
def enable_rls_on_routes(schema_editor):
    """Enable Row-Level Security on routes table with ownership policies."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    
    with schema_editor.connection.cursor() as cursor:
        # Enable RLS
        cursor.execute("ALTER TABLE routes ENABLE ROW LEVEL SECURITY;")
        
        # Policy: SELECT
        cursor.execute("""
            CREATE POLICY routes_owner_select ON routes
                FOR SELECT
                USING (user_id = current_setting('app.user_id', true)::bigint);
        """)
        
        # Policy: INSERT
        cursor.execute("""
            CREATE POLICY routes_owner_insert ON routes
                FOR INSERT
                WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
        """)
        
        # Policy: UPDATE
        cursor.execute("""
            CREATE POLICY routes_owner_update ON routes
                FOR UPDATE
                USING (user_id = current_setting('app.user_id', true)::bigint)
                WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
        """)
        
        # Policy: DELETE
        cursor.execute("""
            CREATE POLICY routes_owner_delete ON routes
                FOR DELETE
                USING (user_id = current_setting('app.user_id', true)::bigint);
        """)

def disable_rls_on_routes(schema_editor):
    """Remove RLS policies from routes table (for rollback)."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP POLICY IF EXISTS routes_owner_select ON routes;")
        cursor.execute("DROP POLICY IF EXISTS routes_owner_insert ON routes;")
        cursor.execute("DROP POLICY IF EXISTS routes_owner_update ON routes;")
        cursor.execute("DROP POLICY IF EXISTS routes_owner_delete ON routes;")
        cursor.execute("ALTER TABLE routes DISABLE ROW LEVEL SECURITY;")
```

### Phase 4: Generate Initial Migrations

**Command**:
```bash
python manage.py makemigrations
```

This creates auto-generated migration files like `0001_initial.py` for each app.

### Phase 5: Enhance Migrations with Raw SQL

**Edit each generated migration** to add `RunPython` operations for advanced features.

**Critical order rules**:
1. Table creation (`CreateModel`) must come BEFORE RLS policies
2. Database functions must be created BEFORE triggers that use them
3. Tables must exist BEFORE indexes on them
4. RLS policies should be AFTER all table structure is complete

**Example migration structure**:
```python
# pathie/apps/routes/migrations/0001_initial.py
from django.db import migrations, models
import django.db.models.deletion
from pathie.apps.core.sql.rls_policies import (
    enable_rls_on_routes, 
    disable_rls_on_routes
)

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        # First: Create table structure
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('status', models.CharField(
                    max_length=20, 
                    choices=[('temporary', 'Temporary'), ('saved', 'Saved')]
                )),
                ('route_type', models.CharField(
                    max_length=20,
                    choices=[('ai_generated', 'AI Generated'), ('manual', 'Manual')]
                )),
                ('saved_at', models.DateTimeField(blank=True, null=True)),
                ('cached_at', models.DateTimeField(blank=True, null=True)),
                ('cache_expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='routes',
                    to='auth.user',
                    db_column='user_id'
                )),
            ],
            options={
                'db_table': 'routes',
            },
        ),
        
        # Add basic indexes (Django handles these)
        migrations.AddIndex(
            model_name='route',
            index=models.Index(
                fields=['user', 'status', '-created_at'],
                name='routes_idx_user_status_created'
            ),
        ),
        migrations.AddIndex(
            model_name='route',
            index=models.Index(fields=['route_type'], name='routes_idx_route_type'),
        ),
        
        # Then: Apply RLS policies (requires table to exist)
        migrations.RunPython(
            enable_rls_on_routes,
            reverse_code=disable_rls_on_routes,
        ),
    ]
```

### Phase 6: Create Separate Migration for Shared Database Functions

**Create empty migration**:
```bash
python manage.py makemigrations --empty core --name create_database_functions
```

**Implement**:
```python
# pathie/apps/core/migrations/0001_create_database_functions.py
from django.db import migrations
from pathie.apps.core.sql.functions import (
    create_set_updated_at_function,
    drop_set_updated_at_function,
)

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    
    operations = [
        migrations.RunPython(
            create_set_updated_at_function,
            reverse_code=drop_set_updated_at_function,
        ),
    ]
```

### Phase 7: Create Migration for Triggers

**Create empty migration**:
```bash
python manage.py makemigrations --empty routes --name add_triggers
```

**Implement**:
```python
# pathie/apps/routes/migrations/0002_add_triggers.py
from django.db import migrations
from pathie.apps.core.sql.triggers import (
    create_updated_at_trigger_for_routes,
    drop_updated_at_trigger_for_routes,
)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_create_database_functions'),
        ('routes', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(
            create_updated_at_trigger_for_routes,
            reverse_code=drop_updated_at_trigger_for_routes,
        ),
    ]
```

### Phase 8: Create Migrations for Complex Constraints

For triggers that enforce business logic (like route_tags_limit, route_points_limit), create similar migrations following the same pattern.

## Critical Implementation Rules

### ✅ DO:
1. **Always provide reverse_code** for `RunPython` operations
2. **Always check vendor** (`if schema_editor.connection.vendor != 'postgresql': return`)
3. **Use CASCADE in DROP statements** when removing functions that have dependent triggers
4. **Document RLS/trigger presence** in model docstrings
5. **Test rollback** for every migration: `migrate app_name NNNN` (backwards), then forward again
6. **Use explicit index names** matching SQL file exactly
7. **Set proper dependencies** between migrations (especially for shared functions)
8. **Use transactions implicitly** (Django wraps migrations in transactions by default)

### ❌ DON'T:
1. **Don't use `migrations.RunSQL`** without `reverse_sql` parameter
2. **Don't create triggers before functions** they depend on
3. **Don't apply RLS before table creation**
4. **Don't hardcode SQL in migration files** – extract to sql/ module for reusability
5. **Don't forget `db_column='user_id'`** when Django field name differs from SQL column
6. **Don't use SQLite for testing** RLS-enabled code (it will silently pass without testing RLS)
7. **Don't modify `updated_at` manually** when auto_now=True (conflicts with trigger)

## File Organization Pattern

```
pathie/
├── apps/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_create_database_functions.py
│   │   └── sql/
│   │       ├── __init__.py
│   │       ├── functions.py
│   │       ├── triggers.py
│   │       ├── rls_policies.py
│   │       ├── constraints.py
│   │       └── indexes.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── models.py              # Route, RoutePoint models
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   ├── 0001_initial.py   # Tables + RLS
│   │   │   └── 0002_add_triggers.py
│   ├── places/
│   │   ├── __init__.py
│   │   ├── models.py              # Place, PlaceDescription models
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   ├── 0001_initial.py
│   │   │   └── 0002_add_fulltext_indexes.py
│   ├── tags/
│   │   ├── __init__.py
│   │   ├── models.py              # Tag model
│   │   └── migrations/
│   │       ├── __init__.py
│   │       └── 0001_initial.py
│   └── ratings/
│       ├── __init__.py
│       ├── models.py              # Rating model
│       └── migrations/
│           ├── __init__.py
│           └── 0001_initial.py
└── manage.py
```

## Testing Strategy

### Test Configuration
**Use PostgreSQL for tests**, not SQLite:

```python
# pathie/settings_test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_pathie',
        'USER': 'pathie',
        'PASSWORD': 'secret',
        'HOST': 'localhost',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_pathie',
        },
    }
}
```

### Rollback Testing
After creating each migration, test rollback:
```bash
python manage.py migrate routes 0002  # Forward
python manage.py migrate routes 0001  # Rollback
python manage.py migrate routes 0002  # Forward again
```

## Deployment

**Docker Compose integration** – standard approach works without changes:

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: pathie
      POSTGRES_USER: pathie
      POSTGRES_PASSWORD: secret
  
  app:
    build: .
    depends_on:
      - db
    command: python manage.py migrate && python manage.py runserver 0.0.0.0:8000
```

**Deployment command**:
```bash
docker-compose run --rm app python manage.py migrate
```

This single command will:
1. ✅ Create all tables from models.py
2. ✅ Apply all custom SQL (functions, triggers, RLS)
3. ✅ Execute migrations in correct dependency order
4. ✅ Handle atomic transactions properly

## Middleware for RLS Session Variables

**Critical**: Create middleware to set `app.user_id` session variable for RLS:

```python
# pathie/apps/core/middleware.py
from django.db import connection

class SetPostgresUserContextMiddleware:
    """
    Sets PostgreSQL session variable 'app.user_id' for Row-Level Security.
    
    This must run BEFORE any database queries in request processing.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('app.user_id', %s, true)",
                    [str(request.user.pk)]
                )
        
        response = self.get_response(request)
        return response
```

**Register in settings**:
```python
# pathie/settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'pathie.apps.core.middleware.SetPostgresUserContextMiddleware',  # ← Add here
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## Implementation Checklist

For each table in the SQL schema, follow this checklist:

- [ ] Create Django model in `models.py` with appropriate app
- [ ] Add `db_table` in `Meta` to match SQL table name
- [ ] Map all columns to Django fields with correct types
- [ ] Add `choices` for CHECK constraints with IN (...)
- [ ] Add basic indexes via `Meta.indexes`
- [ ] Add docstring documenting RLS/triggers if applicable
- [ ] Run `python manage.py makemigrations`
- [ ] If table needs RLS: create function in `sql/rls_policies.py`
- [ ] If table needs RLS: add `RunPython` operation to migration after `CreateModel`
- [ ] If table needs triggers: ensure functions exist (dependency)
- [ ] If table needs triggers: create trigger migration with proper dependencies
- [ ] If table needs full-text search: create GIN index via `RunPython`
- [ ] If table needs partial unique index: create via `RunPython`
- [ ] Test migration forward: `python manage.py migrate`
- [ ] Test migration rollback: `python manage.py migrate app_name NNNN-1`
- [ ] Verify table exists in database: `\dt` in psql
- [ ] Verify RLS is enabled: `SELECT tablename FROM pg_tables WHERE rowsecurity = true;`
- [ ] Verify policies exist: `SELECT * FROM pg_policies WHERE tablename = 'table_name';`

## Common Pitfalls to Avoid

1. **Trigger without function**: Always create function migration before trigger migration
2. **RLS without middleware**: RLS will block ALL queries if `app.user_id` is not set
3. **Forgetting reverse_code**: Migration cannot be rolled back, breaking development workflow
4. **SQLite in tests**: RLS features silently ignored, giving false confidence
5. **Modifying auto_now field manually**: Conflicts with updated_at trigger
6. **Not using CASCADE in DROP FUNCTION**: Trigger remains orphaned, causing errors
7. **Wrong dependency order**: Migration tries to use function that doesn't exist yet

## Success Criteria

Your implementation is successful when:

✅ `python manage.py migrate` completes without errors  
✅ `python manage.py migrate app_name zero` rolls back completely  
✅ `SELECT * FROM pg_policies;` shows all expected RLS policies  
✅ `SELECT * FROM pg_trigger;` shows all expected triggers  
✅ Queries as authenticated user see only their own data (RLS working)  
✅ `python manage.py inspectdb` shows structure matching models.py (for basic fields)  
✅ All tests pass using PostgreSQL test database  
✅ `docker-compose up` deploys complete schema successfully  

---

**Final Note**: This is a pragmatic compromise, not a pure solution. You're accepting the complexity of maintaining schema in two places (models.py + migration SQL) in exchange for the power of advanced PostgreSQL features while keeping Django ORM conveniences. Document heavily, test thoroughly, and enforce team discipline through code reviews.