# 02 — HTML5 + Jinja2 (Templating)

## Ye folder kya hai?

**Label folder** — HTML pages Flask ke templates engine **Jinja2** se dynamic hoti hain.

## Asal files kahan hain?

`expense_tracker/templates/`

| File | Purpose |
|------|---------|
| `base.html` | Parent layout: navbar, flash messages, `{% block %}` hooks |
| `auth/login.html`, `auth/register.html` | Auth forms |
| `dashboard.html` | KPI + chart canvas |
| `transactions/list.html` | History + filters |
| `transactions/form.html` | Add/Edit transaction |

## Jinja2 features used

- `{% extends "base.html" %}` — template inheritance
- `{{ variable }}` — server se values render
- `{% url_for(...) %}` — safe URL generation
- `{% if %}`, `{% for %}` — control flow
- `{# ... #}` — comments (teacher explanation ke liye templates mein add kiye gaye)
