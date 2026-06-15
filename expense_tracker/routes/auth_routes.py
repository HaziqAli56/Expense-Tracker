"""
Backward-compatible authentication blueprint import.

The canonical authentication controller now lives in expense_tracker.routes.auth
to match the modular route naming requested for the project.
"""

from expense_tracker.routes.auth import auth_bp


__all__ = ["auth_bp"]
