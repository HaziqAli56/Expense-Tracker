"""
Project entry point (Flask development server).

Ye file project root par hai taake CMD mein seedha chal sake:
    python run.py

Asal application factory `expense_tracker` package ke andar hai.
"""

from expense_tracker import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True sirf development ke liye; production mein WSGI server use hota hai
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
