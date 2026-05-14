# 03 — CSS3 (Custom styles)

## Ye folder kya hai?

**Label folder** — custom stylesheet alag file mein hai taake Bootstrap default ke sath mix ho.

## Asal file

`expense_tracker/static/css/style.css`

## Link kahan se hota hai?

`expense_tracker/templates/base.html` mein:

`url_for('static', filename='css/style.css')`

Flask `static/` folder se files serve karta hai.
