import os
import pytesseract
from expense_tracker import create_app, db

# --- Tesseract Configuration (Start) ---
# Check if running on Render (Render sets this variable automatically)
if os.environ.get('RENDER'):
    # Cloud (Render) Linux path
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
else:
    # Local (Windows) path from .env
    tesseract_path = os.environ.get('TESSERACT_CMD')
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
# --- Tesseract Configuration (End) ---

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables ensured.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)