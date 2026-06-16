# run.py
from expense_tracker import create_app, db
from expense_tracker.models.user_model import User 
from expense_tracker.models.transaction_model import Transaction 
import datetime

app = create_app()

with app.app_context():
    db.create_all() # Yeh naya expenses_v2.db banayega
    
    # Aapki email address
    my_email = 'shaikhmuhammad603@gmail.com'
    
    # 1. User check karo
    sadiq = User.query.filter_by(email=my_email).first()
    
    # 2. Agar user nahi mila, toh NAYA USER banao
    if not sadiq:
        print("User not found. Creating user...")
        sadiq = User(
            full_name='Muhammad Sadiq Ali',
            email=my_email,
            username=my_email, # Registration logic mein username = email hai
        )
        sadiq.set_password('Sadiqisgr8@') # Login karte waqt ye password use karna
        db.session.add(sadiq)
        db.session.commit()
        print("User successfully created!")

    # 3. Ab Data seed karo (agar pehle se data nahi hai)
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
        print("Data successfully seeded!")
    else:
        print("Data is already present, no seeding needed.")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)