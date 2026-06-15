"""
Backward compatibility: pehle tum `python app.py` se chala rahe the.

Ab recommended entry `run.py` hai, lekin purani command bhi kaam karti rahe.
"""

from expense_tracker import create_app, db # Yahan 'db' import karna zaroori hai

app = create_app()

# Database auto-migration logic
with app.app_context():
    try:
        # Check karte hain ki 'sub_category' column exist karta hai ya nahi
        db.engine.execute("SELECT sub_category FROM transactions LIMIT 1")
    except:
        # Agar error aaya (matlab column missing hai), toh ye command chalegi
        print("Updating database schema: Adding sub_category column...")
        try:
            db.engine.execute("ALTER TABLE transactions ADD COLUMN sub_category VARCHAR(100)")
            print("Database Updated: sub_category column added successfully!")
        except Exception as e:
            print(f"Error updating database: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)