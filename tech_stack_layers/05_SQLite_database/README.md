# 05 — SQLite (Relational Database)

## Ye folder kya hai?

**Label folder** — SQLite file-based database; separate server install nahi.

## Database file location

`instance/expenses.db` (project root ke `instance/` folder mein)

- Pehli run par `create_app()` `instance/` folder ensure karta hai
- `db.create_all()` tables banata hai (`users`, `transactions`)

## Connection string kahan set hai?

`expense_tracker/config.py` → `SQLALCHEMY_DATABASE_URI`

## Tables map

- ORM classes: `expense_tracker/models/user_model.py`, `transaction_model.py`
- SQLAlchemy migrations is demo mein optional; university scope mein `create_all()` enough hai
