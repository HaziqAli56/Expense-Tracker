from expense_tracker import create_app, db

app = create_app()

with app.app_context():
    # Yahan bhi sirf creation hoga, data delete nahi hoga
    db.create_all()
    print("Database ready!")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)