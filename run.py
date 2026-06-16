from expense_tracker import create_app, db

app = create_app()

# Yeh code Render par chalega kyunki Render run.py ko hit karta hai
with app.app_context():
    try:
        db.drop_all()  # Purani tables delete
        db.create_all() # Nayi tables create (sub_category ke sath)
        print("Database successfully reset from run.py!")
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)