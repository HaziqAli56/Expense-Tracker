# 01 — Python (Flask) + Flask-SQLAlchemy (ORM)

## Ye folder kya hai?

Teacher demo ke liye **label folder**: is path mein README hai taake tum stack alag alag explain kar sako.

## Asal code kahan hai?

| Layer | Path |
|------|------|
| Flask app factory + blueprint register | `expense_tracker/__init__.py` |
| Config (SECRET_KEY, SQLite URI) | `expense_tracker/config.py` |
| Extensions (`db`, `login_manager`) | `expense_tracker/extensions.py` |
| Constants | `expense_tracker/constants.py` |
| Routes (Controller) | `expense_tracker/routes/*.py` |
| Models (ORM ↔ SQLite tables) | `expense_tracker/models/*.py` |
| Helpers | `expense_tracker/utils/*.py` |

## Run entry

- `run.py` (recommended)
- `app.py` (same app — backward compatibility)

## MVC short

- **Model:** `expense_tracker/models/`
- **View:** `expense_tracker/templates/`
- **Controller:** `expense_tracker/routes/`
