# Alembic Migrations for ResTrack

This directory contains the Alembic migration environment for the ResTrack application's local database (`restrack.db`). Alembic is used to manage schema changes and data migrations in a safe, versioned, and repeatable way.

## Quick Start

### 1. Activate your virtual environment
```
.venv\Scripts\activate  # Windows
source .venv/bin/activate # Linux/Mac
```

### 2. Set the database environment variable
Make sure the `DB_RESTRACK` environment variable points to your SQLite database (default is `sqlite:///data/restrack.db`).

```
$env:DB_RESTRACK="sqlite:///data/restrack.db"  # PowerShell
export DB_RESTRACK="sqlite:///data/restrack.db" # Bash
```

### 3. Creating a new migration
Autogenerate a migration after changing models (e.g., adding a column):

```
alembic revision --autogenerate -m "Describe your change here"
```

### 4. Applying migrations
Apply all pending migrations to the database:

```
alembic upgrade head
```

## How Alembic is Configured
- The database URL is loaded from the `DB_RESTRACK` environment variable (see `env.py`).
- All models are imported from `restrack.models` and `target_metadata` is set to `SQLModel.metadata` for autogeneration.
- Migration scripts are stored in `alembic/versions/`.

## Special Notes for SQLite
- SQLite has limited ALTER TABLE support. Some operations (like changing column types or dropping columns) may not work and require manual migration steps.
- When adding a NOT NULL column, always provide a `server_default` value in the migration script.
- If you see errors about existing tables or columns, check if the database was created before Alembic was set up. You may need to manually adjust the schema or migration scripts.

## Common Migration Tasks

### Add a New Column
1. Update your model in `restrack/models/`.
2. Run:
   ```
   alembic revision --autogenerate -m "Add <column> to <table>"
   alembic upgrade head
   ```
3. If adding a NOT NULL column, ensure you set a default value in the migration script for SQLite.

### Manual Data Migrations
You can write Python code in migration scripts to update or migrate data. Use the `op.get_bind()` method to get a SQLAlchemy connection.

Example:
```python
from alembic import op
import sqlalchemy as sa

conn = op.get_bind()
conn.execute(sa.text("UPDATE user SET must_change_password = 1 WHERE ..."))
```

## Troubleshooting
- **Database locked**: Make sure no other process is using the database.
- **Cannot add NOT NULL column**: Add a `server_default` in the migration script.
- **Table already exists**: Remove or comment out the `op.create_table` call for that table in the migration script.
- **Type change not supported**: For SQLite, you may need to create a new table, copy data, and drop the old table.

## Further Reading
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

For questions, see the main project README or contact the ResTrack maintainers.
