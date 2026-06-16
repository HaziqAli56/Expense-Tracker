from expense_tracker import create_app, db

app = create_app()

with app.app_context():
    # Sirf tables create hongi agar nahi bani hain, delete kuch nahi hoga
    db.create_all()
    print("Database tables ensured.")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)