import os
import pytesseract
from expense_tracker import create_app, db

app = create_app()

# Tesseract OCR setup for both Local (Windows) and Cloud (Render/Linux)
# Render par Environment Variable set hai, local par .env use hoga
tesseract_path = os.environ.get('TESSERACT_CMD')

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    # Default fallback for local windows if not set in .env
    # Agar path sahi nahi hua, toh bhi error nahi aayega
    pass

with app.app_context():
    # Database tables create karna
    db.create_all()
    print("Database tables ensured.")

if __name__ == "__main__":
    # Render par port variable dynamic hota hai, wahan 5000 fix na rakhein
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)