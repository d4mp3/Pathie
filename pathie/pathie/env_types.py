"""
Type definitions for environment variables used in the Pathie project.

This module provides type-safe access to environment variables using django-environ.
It serves a similar purpose to env.d.ts in frontend projects, ensuring type safety
and early validation of configuration values.

Usage:
    In settings.py:
    >>> from pathie.env_types import get_env
    >>> env = get_env()
    >>> DEBUG = env.debug
    >>> DATABASE_URL = env.database_url
"""

from typing import TypedDict, Literal
from dataclasses import dataclass
import environ
import os


# Type definitions for environment variable casting
class DatabaseConfig(TypedDict):
    """Type definition for parsed DATABASE_URL."""

    ENGINE: str
    NAME: str
    USER: str
    PASSWORD: str
    HOST: str
    PORT: str


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass(frozen=True)
class EnvironmentVariables:
    """
    Type-safe environment variables for the Pathie project.

    All environment variables are defined here with their expected types.
    This ensures mypy can type-check configuration access throughout the project.
    """

    # Django Core Settings
    debug: bool
    secret_key: str
    allowed_hosts: list[str]

    # Database Configuration (individual components)
    sql_engine: str
    sql_database: str
    sql_user: str
    sql_password: str
    sql_host: str
    sql_port: int

    # Database Configuration (parsed URL)
    database_config: DatabaseConfig

    # PostgreSQL Container Settings
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database: str

    # Optional External Services
    openai_api_key: str | None

    # Development Settings
    django_log_level: LogLevel
    sql_debug: bool


def get_env() -> EnvironmentVariables:
    """
    Initialize and validate environment variables.

    This function reads the .env file and validates all required variables.
    It will raise an error early if any required variables are missing or invalid.

    Returns:
        EnvironmentVariables: Type-safe environment configuration

    Raises:
        environ.ImproperlyConfigured: If required variables are missing

    Example:
        >>> env = get_env()
        >>> print(env.debug)  # mypy knows this is a bool
        >>> print(env.sql_port)  # mypy knows this is an int
    """
    # Initialize environ with type definitions and defaults
    env = environ.Env(
        # Django Core
        DEBUG=(bool, False),
        SECRET_KEY=(str, ""),  # Required, no default in production
        DJANGO_ALLOWED_HOSTS=(list, []),
        # Database - Individual Components
        SQL_ENGINE=(str, "django.db.backends.postgresql"),
        SQL_DATABASE=(str, ""),
        SQL_USER=(str, ""),
        SQL_PASSWORD=(str, ""),
        SQL_HOST=(str, "localhost"),
        SQL_PORT=(int, 5432),
        # PostgreSQL Container
        POSTGRES_USER=(str, "postgres"),
        POSTGRES_PASSWORD=(str, ""),
        POSTGRES_DB=(str, ""),
        DATABASE=(str, "postgres"),
        # Optional Services
        OPENAI_API_KEY=(str, None),
        # Development
        DJANGO_LOG_LEVEL=(str, "INFO"),
        SQL_DEBUG=(bool, False),
    )

    # Read .env file if it exists
    # Determine BASE_DIR (project root)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(BASE_DIR, "..", ".env")

    if os.path.exists(env_file):
        environ.Env.read_env(env_file)

    # Parse DATABASE_URL if provided, otherwise construct from individual components
    database_config: DatabaseConfig
    if "DATABASE_URL" in os.environ:
        # Parse DATABASE_URL using django-environ
        db_config = env.db()
        database_config = {
            "ENGINE": db_config["ENGINE"],
            "NAME": db_config["NAME"],
            "USER": db_config["USER"],
            "PASSWORD": db_config["PASSWORD"],
            "HOST": db_config["HOST"],
            "PORT": db_config["PORT"],
        }
    else:
        # Construct from individual SQL_* variables
        database_config = {
            "ENGINE": env("SQL_ENGINE"),
            "NAME": env("SQL_DATABASE"),
            "USER": env("SQL_USER"),
            "PASSWORD": env("SQL_PASSWORD"),
            "HOST": env("SQL_HOST"),
            "PORT": str(env("SQL_PORT")),
        }

    # Validate log level
    log_level = env("DJANGO_LOG_LEVEL")
    valid_log_levels: tuple[LogLevel, ...] = (
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    )
    if log_level not in valid_log_levels:
        raise ValueError(
            f"Invalid DJANGO_LOG_LEVEL: {log_level}. "
            f"Must be one of: {', '.join(valid_log_levels)}"
        )

    # Return type-safe configuration
    return EnvironmentVariables(
        # Django Core
        debug=env("DEBUG"),
        secret_key=env("SECRET_KEY"),
        allowed_hosts=env.list("DJANGO_ALLOWED_HOSTS"),
        # Database - Individual
        sql_engine=env("SQL_ENGINE"),
        sql_database=env("SQL_DATABASE"),
        sql_user=env("SQL_USER"),
        sql_password=env("SQL_PASSWORD"),
        sql_host=env("SQL_HOST"),
        sql_port=env("SQL_PORT"),
        # Database - Parsed
        database_config=database_config,
        # PostgreSQL Container
        postgres_user=env("POSTGRES_USER"),
        postgres_password=env("POSTGRES_PASSWORD"),
        postgres_db=env("POSTGRES_DB"),
        database=env("DATABASE"),
        # Optional
        openai_api_key=env("OPENAI_API_KEY"),
        # Development
        django_log_level=log_level,  # type: ignore
        sql_debug=env("SQL_DEBUG"),
    )


# Export type-safe getter
__all__ = ["get_env", "EnvironmentVariables", "DatabaseConfig", "LogLevel"]
