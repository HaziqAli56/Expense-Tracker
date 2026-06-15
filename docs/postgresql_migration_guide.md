# PostgreSQL Migration Guide

## 1. Environment Configuration

PostgreSQL is the production database target because it handles concurrent users,
strong data integrity, advanced indexing, JSONB, backups, and operational tooling
far better than SQLite.

Use this `DATABASE_URL` format in `.env`:

```text
DATABASE_URL=postgresql://expense_user:strong_password@localhost/expense_tracker
```

Never hardcode database credentials in Python files. Keep them in `.env` locally
and in your hosting provider's secret manager in production.

## 2. Create The PostgreSQL Database

Open `psql` as a PostgreSQL admin user:

```sql
CREATE DATABASE expense_tracker;
CREATE USER expense_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE expense_tracker TO expense_user;
```

For PostgreSQL 15 and newer, also grant schema privileges after connecting to
the database:

```sql
\c expense_tracker
GRANT ALL ON SCHEMA public TO expense_user;
```

## 3. Install Migration Dependencies

The project requires:

```text
Flask-Migrate==4.1.0
psycopg2-binary==2.9.11
```

Install from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 4. Initialize Flask-Migrate

Set the app entry point first:

```bash
set FLASK_APP=run.py
```

On PowerShell:

```powershell
$env:FLASK_APP = "run.py"
```

Initialize Alembic once:

```bash
flask db init
```

Create the first migration from the SQLAlchemy models:

```bash
flask db migrate -m "initial postgresql schema"
```

Apply it to PostgreSQL:

```bash
flask db upgrade
```

## 5. Moving Existing SQLite Data

For production-like integrity, migrate schema first with Flask-Migrate, then move
data in a controlled export/import step:

1. Back up the SQLite database file.
2. Run `flask db upgrade` against PostgreSQL.
3. Export SQLite rows table by table.
4. Import into PostgreSQL with validated column mappings.
5. Verify record counts and foreign-key relationships.

## 6. Future-Proofing

PostgreSQL allows the app to grow into multi-user workloads because it supports
real concurrent writes, connection pooling, row locks, stronger constraints, and
better indexes than SQLite.

Later scale features fit naturally:

- Redis caching for dashboard summaries and session-like hot data.
- Connection pooling through PgBouncer or the hosting provider.
- Row-level security if tenant/user isolation becomes stricter.
- Point-in-time recovery, logical backups, read replicas, and managed snapshots.
