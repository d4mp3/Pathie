# Environment Variables Setup Guide

This document explains how to configure environment variables for the Pathie project with type-safe PostgreSQL connection settings.

## Quick Start

1. **Copy the appropriate example file:**
   ```bash
   # For development
   cp .env.dev.example .env.dev
   
   # For production
   cp .env.prod.example .env.prod
   cp .env.prod.db.example .env.prod.db
   ```

2. **Edit the `.env` file** with your actual values (especially SECRET_KEY and passwords in production)

3. **Link the active environment:**
   ```bash
   # For development
   ln -sf .env.dev .env
   
   # For production
   ln -sf .env.prod .env
   ```

## Files Created

### Environment Templates

- **`.env.example`** - Comprehensive template with all variables and documentation
- **`.env.dev.example`** - Development environment template
- **`.env.prod.example`** - Production environment template
- **`.env.prod.db.example`** - PostgreSQL container configuration for production

### Type Definitions

- **`pathie/pathie/env_types.py`** - Type-safe environment variable definitions for mypy

## Type-Safe Environment Variables

The project uses `django-environ` for environment variable validation and type casting, similar to `env.d.ts` in frontend projects.

### Usage in settings.py

```python
from pathie.env_types import get_env

# Get type-safe environment configuration
env = get_env()

# mypy knows these types:
DEBUG = env.debug                    # bool
SECRET_KEY = env.secret_key          # str
ALLOWED_HOSTS = env.allowed_hosts    # list[str]
SQL_PORT = env.sql_port             # int

# Database configuration
DATABASES = {
    'default': env.database_config   # DatabaseConfig (TypedDict)
}
```

### Type Definitions

All environment variables are defined in `EnvironmentVariables` dataclass with proper types:

```python
@dataclass(frozen=True)
class EnvironmentVariables:
    # Django Core (with types)
    debug: bool
    secret_key: str
    allowed_hosts: list[str]
    
    # Database (with types)
    sql_port: int
    sql_host: str
    # ... etc
```

### Benefits

1. **Type Safety**: mypy validates environment variable usage at compile time
2. **Early Validation**: Missing or invalid variables raise errors at startup
3. **Auto-completion**: IDEs provide intelligent suggestions
4. **Documentation**: Types serve as inline documentation

## Environment Variables Reference

### Django Core

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEBUG` | `bool` | `False` | Enable debug mode (use `1` or `0`) |
| `SECRET_KEY` | `str` | Required | Django secret key (generate new for production) |
| `DJANGO_ALLOWED_HOSTS` | `list[str]` | `[]` | Space-separated list of allowed hostnames |

### PostgreSQL Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SQL_ENGINE` | `str` | `django.db.backends.postgresql` | Database engine |
| `SQL_DATABASE` | `str` | Required | Database name |
| `SQL_USER` | `str` | Required | Database user |
| `SQL_PASSWORD` | `str` | Required | Database password |
| `SQL_HOST` | `str` | `localhost` | Database host (`db` for Docker) |
| `SQL_PORT` | `int` | `5432` | Database port |

**Alternative**: Use `DATABASE_URL` instead of individual `SQL_*` variables:
```bash
DATABASE_URL=postgres://user:password@host:port/database
```

### PostgreSQL Container (Docker)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POSTGRES_USER` | `str` | `postgres` | PostgreSQL superuser name |
| `POSTGRES_PASSWORD` | `str` | Required | PostgreSQL superuser password |
| `POSTGRES_DB` | `str` | Required | Initial database name |
| `DATABASE` | `str` | `postgres` | Default database for connection |

### Optional Services

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | `str \| None` | `None` | OpenAI API key for AI features |
| `DJANGO_LOG_LEVEL` | `LogLevel` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `SQL_DEBUG` | `bool` | `False` | Enable SQL query logging |

## Security Best Practices

### Development

- Use simple passwords for local development
- Commit `.env.*.example` files, never commit actual `.env` files
- Keep `.env` in `.gitignore`

### Production

1. **Generate a secure SECRET_KEY:**
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **Use strong database passwords:**
   - Minimum 16 characters
   - Mix of letters, numbers, and symbols
   - Different from SECRET_KEY

3. **Set DEBUG=0:**
   - Never run production with DEBUG=1
   - Ensure proper error logging is configured

4. **Configure ALLOWED_HOSTS:**
   - List only your actual production domains
   - Never use `*` wildcard in production

5. **Use environment-specific files:**
   - Keep production credentials separate from development
   - Use Docker secrets or environment variable injection in production

## Validation

The `get_env()` function validates all environment variables at Django startup:

- **Missing required variables** → raises `ImproperlyConfigured`
- **Invalid types** → raises `ValueError`
- **Invalid log levels** → raises `ValueError`

This ensures the application won't start with invalid configuration.

## MyPy Integration

To verify type safety:

```bash
cd pathie
mypy .
```

MyPy will check that all environment variable usage is type-safe based on the definitions in `env_types.py`.

## Example Workflows

### Local Development with Docker

```bash
# 1. Copy development template
cp .env.dev.example .env.dev

# 2. Edit if needed (optional)
nano .env.dev

# 3. Link as active environment
ln -sf .env.dev .env

# 4. Start Docker Compose
docker-compose up
```

### Production Deployment

```bash
# 1. Copy production templates
cp .env.prod.example .env.prod
cp .env.prod.db.example .env.prod.db

# 2. Generate SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' > secret.txt

# 3. Edit .env.prod with secure values
nano .env.prod
# - Update SECRET_KEY
# - Update SQL_PASSWORD
# - Update DJANGO_ALLOWED_HOSTS
# - Set DEBUG=0

# 4. Edit .env.prod.db
nano .env.prod.db
# - Update POSTGRES_PASSWORD (same as SQL_PASSWORD)

# 5. Link as active environment
ln -sf .env.prod .env

# 6. Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### "ImproperlyConfigured: Set the SECRET_KEY environment variable"

- Ensure `.env` file exists and contains `SECRET_KEY=...`
- Check that `.env` is in the correct directory (project root)

### "Connection refused" database errors

- Verify `SQL_HOST` matches your database service name
- For Docker: use `SQL_HOST=db` (service name in docker-compose.yml)
- For local PostgreSQL: use `SQL_HOST=localhost`

### MyPy errors about environment variables

- Ensure you're using `get_env()` function from `env_types.py`
- Check that accessed attributes match the `EnvironmentVariables` dataclass
- Run `mypy pathie/pathie/env_types.py` to verify the types module itself

## References

- [django-environ documentation](https://django-environ.readthedocs.io/)
- [Django database configuration](https://docs.djangoproject.com/en/stable/ref/settings/#databases)
- [PostgreSQL Docker image](https://hub.docker.com/_/postgres)
