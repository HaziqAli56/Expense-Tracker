import os
from flask import Flask
from sqlalchemy import text
from expense_tracker import create_app, db

app = create_app()

with app.app_context():
    # 1. Database file path check karo (apni file ka sahi naam dena)
    db_path = 'expense.db' # Agar folder mein hai toh 'instance/expense.db' check karo
    
    # 2. Agar purana structure problem kar raha hai, toh file delete karo
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Old database deleted successfully.")
        except Exception as e:
            print(f"Could not delete database: {e}")
    
    # 3. Nayi database aur tables banao
    db.create_all()
    print("New database created with updated schema.")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)