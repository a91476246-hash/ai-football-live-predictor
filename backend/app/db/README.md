# db — Database layer

Async SQLAlchemy 2.0 layer.

## Files

| File | Purpose |
|---|---|
| `base.py` | Declarative base, `TimestampedMixin`. |
| `session.py` | Engine, `async_sessionmaker`, `session_scope` context manager, FastAPI `get_db` dependency. |
| `init_db.py` | `create_all` for dev (use Alembic in production). |

## Switching to PostgreSQL

Set `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname` and restart. No code changes required.

## Migrations

For dev we rely on `metadata.create_all`. For production wire up Alembic — the `Base.metadata` is in `app.db.base`.
