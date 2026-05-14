"""
Shared Flask extensions — ek hi `db` aur `login_manager` poori app mein use ho.

Kyun alag file?
- routes aur models dono `db` import karte hain; agar har file mein naya SQLAlchemy()
  banayein to circular import / double registration ho sakti hai.
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# ORM handle: models isi `db.Model` se inherit karte hain
db = SQLAlchemy()

# Login state: current_user, @login_required, login_user, etc.
login_manager = LoginManager()
# Agar protected URL par guest aaye to yahan redirect (endpoint name)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
