from expense_tracker import create_app, db

app = create_app()

with app.app_context():
    try:
        # 1. Purani saari tables ko database se uda do
        db.drop_all()
        print("Success: Old tables dropped.")
        
        # 2. Naye structure ke hisaab se fresh tables bana do
        db.create_all()
        print("Success: New tables created with sub_category.")
    except Exception as e:
        print(f"Database reset error: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)