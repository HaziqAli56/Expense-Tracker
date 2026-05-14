ra # Expense Tracker — Project Technical Guide (University / Viva)

Ye document **pure project** ka map hai: kaunsi technology kahan use hui, MVC flow, aur important files/functions kis kaam ke hain.

---

## 1) Project root (run + dependencies)

| File / folder | Kaam |
|---------------|------|
| `run.py` | **Main entry**: `create_app()` call karke development server start (`python run.py`). |
| `app.py` | **Same app** — backward compatibility (`python app.py` bhi chal sakta hai). |
| `requirements.txt` | Python libraries list (`pip install -r requirements.txt`). |
| `instance/` | SQLite DB file location (`expenses.db` yahan banegi). |
| `expense_tracker/` | Poora Flask package (backend + templates + static). |
| `tech_stack_layers/` | Teacher demo folders: har technology ka **README pointer** (code duplicate nahi). |
| `documentation/` | Ye guide + extra notes. |

---

## 2) Tech stack → folders (teacher explanation order)

1. **Python + Flask + Flask-SQLAlchemy** → `tech_stack_layers/01_.../README.md` + code `expense_tracker/`
2. **HTML5 + Jinja2** → `tech_stack_layers/02_.../README.md` + `expense_tracker/templates/`
3. **CSS3** → `tech_stack_layers/03_.../README.md` + `expense_tracker/static/css/style.css`
4. **Bootstrap** → `tech_stack_layers/04_.../README.md` + CDN links in `base.html` + `static/README_Bootstrap_CDN.txt`
5. **SQLite** → `tech_stack_layers/05_.../README.md` + `instance/expenses.db`
6. **JavaScript** → `tech_stack_layers/06_.../README.md` + `expense_tracker/static/js/transaction_form.js`

---

## 3) MVC (Model–View–Controller)

- **Model (SQLite tables via ORM)**  
  - `expense_tracker/models/user_model.py` → table `users`  
  - `expense_tracker/models/transaction_model.py` → table `transactions` (FK `user_id` → `users.id`)

- **View (HTML + Jinja2)**  
  - `expense_tracker/templates/**` → user interface pages

- **Controller (Flask routes / business flow)**  
  - `expense_tracker/routes/auth_routes.py` → register/login/logout  
  - `expense_tracker/routes/dashboard_routes.py` → `/` dashboard totals + chart JSON  
  - `expense_tracker/routes/transaction_routes.py` → `/transactions/...` CRUD + filters

---

## 4) Important Python modules (short)

### `expense_tracker/__init__.py` — `create_app()`

- Flask app banata hai, `Config` load karta hai.
- `db.init_app`, `login_manager.init_app`.
- `@login_manager.user_loader` → session se user id le kar DB se `User` object return.
- Blueprints register.
- `db.create_all()` → tables create (SQLite).

### `expense_tracker/config.py`

- `PROJECT_ROOT` + `INSTANCE_DIR` paths.
- `SQLALCHEMY_DATABASE_URI` → SQLite file URI.
- `SECRET_KEY` → sessions secure karne ke liye (dev default weak hai; production mein change).

### `expense_tracker/extensions.py`

- `db = SQLAlchemy()` → ORM entrypoint.
- `login_manager = LoginManager()` → auth/session integration.

### `expense_tracker/constants.py`

- Category whitelists (server-side validation + dropdown source).

### `expense_tracker/utils/chart_helpers.py` — `expenses_by_category(...)`

- Expenses ko category par sum karke Chart.js ke liye `{labels, values}` dict banata hai.

---

## 5) Routes (URLs) — quick list

| URL | Handler | Login? |
|-----|---------|--------|
| `/register` | `auth.register` | guest |
| `/login` | `auth.login` | guest |
| `/logout` | `auth.logout` | yes |
| `/` | `dashboard.home` | yes |
| `/transactions/` | `transactions.list_transactions` | yes |
| `/transactions/add` | `transactions.add` | yes |
| `/transactions/<id>/edit` | `transactions.edit` | yes |
| `/transactions/<id>/delete` (POST) | `transactions.delete` | yes |

---

## 6) Security notes (viva points)

- Password **hash** store (`werkzeug.security`), plain password DB mein nahi.
- Transactions queries mein **`user_id=current_user.id`** filter — user apni rows ke ilawa access na kar sake.
- `@login_required` protected pages par lagaya gaya.

---

## 7) Run commands (CMD)

```bat
cd /d "D:\Downloads\sadiq project"
python -m pip install -r requirements.txt
python run.py
```

Browser: `http://127.0.0.1:5000`

---

## 8) File-by-file index (high level)

**Package**

- `expense_tracker/__init__.py` — app factory + blueprint wiring  
- `expense_tracker/config.py` — settings + SQLite path  
- `expense_tracker/extensions.py` — `db`, `login_manager`  
- `expense_tracker/constants.py` — categories  

**Models**

- `expense_tracker/models/user_model.py` — `User` + password helpers + relationship  
- `expense_tracker/models/transaction_model.py` — `Transaction` fields + FK  

**Routes**

- `expense_tracker/routes/auth_routes.py` — auth blueprint  
- `expense_tracker/routes/dashboard_routes.py` — dashboard blueprint  
- `expense_tracker/routes/transaction_routes.py` — transactions blueprint + CRUD  

**Templates**

- `expense_tracker/templates/base.html` — layout + Bootstrap CDN + blocks  
- `expense_tracker/templates/auth/*.html` — login/register  
- `expense_tracker/templates/dashboard.html` — KPI + Chart.js  
- `expense_tracker/templates/transactions/*.html` — list + form  

**Static**

- `expense_tracker/static/css/style.css` — custom CSS  
- `expense_tracker/static/js/transaction_form.js` — category toggle UX  

---

End of guide.
