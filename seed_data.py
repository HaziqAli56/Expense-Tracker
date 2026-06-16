import os
from expense_tracker import create_app, db
from expense_tracker.models.user_model import User
from expense_tracker.models.transaction_model import Transaction
import datetime

# Flask app initialize karein
app = create_app()

def run_seed():
    with app.app_context():
        # Credentials ko env variable se uthayein (Security ke liye best practice)
        my_email = os.getenv('ADMIN_EMAIL', 'shaikhmuhammad603@gmail.com')
        password = os.getenv('ADMIN_PASSWORD', 'Sadiqisgr8@')

        # Database tables ensure karein (expenses_v2.db create ho jayegi)
        db.create_all()

        # 1. User check/create
        sadiq = User.query.filter_by(email=my_email).first()

        if not sadiq:
            print("Creating user...")
            sadiq = User(full_name='Muhammad Sadiq Ali', email=my_email, username=my_email)
            sadiq.set_password(password)
            db.session.add(sadiq)
            db.session.commit()
            print("User created successfully!")
        else:
            print("User already exists.")

        # 2. Data seeding check
        if not Transaction.query.filter_by(user_id=sadiq.id).first():
            print("Seeding dummy data...")
            dummy_data = [
                # Jan Data
                Transaction(user_id=sadiq.id, amount=50000, entry_type='Income', category='Salary', sub_category='Main Job', description='Jan Salary', entry_date=datetime.date(2026, 1, 5)),
                Transaction(user_id=sadiq.id, amount=12000, entry_type='Expense', category='Food', sub_category='Groceries', description='Monthly Grocery', entry_date=datetime.date(2026, 1, 10)),
                # Feb Data
                Transaction(user_id=sadiq.id, amount=50000, entry_type='Income', category='Salary', sub_category='Main Job', description='Feb Salary', entry_date=datetime.date(2026, 2, 5)),
                Transaction(user_id=sadiq.id, amount=8000, entry_type='Expense', category='Travel', sub_category='Fuel', description='Bike Fuel', entry_date=datetime.date(2026, 2, 15)),
                # Mar Data
                Transaction(user_id=sadiq.id, amount=55000, entry_type='Income', category='Salary', sub_category='Main Job', description='Mar Salary', entry_date=datetime.date(2026, 3, 5)),
                Transaction(user_id=sadiq.id, amount=15000, entry_type='Expense', category='Bills', sub_category='Electricity', description='Electricity Bill', entry_date=datetime.date(2026, 3, 20)),
                # Apr Data
                Transaction(user_id=sadiq.id, amount=20000, entry_type='Income', category='Freelance', sub_category='Projects', description='App Project', entry_date=datetime.date(2026, 4, 10)),
                Transaction(user_id=sadiq.id, amount=5000, entry_type='Expense', category='Shopping', sub_category='Clothes', description='New Shirt', entry_date=datetime.date(2026, 4, 12)),
                # May Data
                Transaction(user_id=sadiq.id, amount=50000, entry_type='Income', category='Salary', sub_category='Main Job', description='May Salary', entry_date=datetime.date(2026, 5, 5)),
                Transaction(user_id=sadiq.id, amount=3000, entry_type='Expense', category='Food', sub_category='Restaurant', description='Dinner', entry_date=datetime.date(2026, 5, 25)),
                # June Data
                Transaction(user_id=sadiq.id, amount=50000, entry_type='Income', category='Salary', sub_category='Main Job', description='June Salary', entry_date=datetime.date(2026, 6, 2)),
                Transaction(user_id=sadiq.id, amount=2000, entry_type='Expense', category='Entertainment', sub_category='Movies', description='Movie', entry_date=datetime.date(2026, 6, 10)),
            ]
            db.session.add_all(dummy_data)
            db.session.commit()
            print("Data seeded successfully!")
        else:
            print("Data already present in database.")

if __name__ == "__main__":
    run_seed()