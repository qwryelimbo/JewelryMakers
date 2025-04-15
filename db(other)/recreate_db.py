import os
from app import app, db

def recreate_database():
    with app.app_context():
        # Get the database file path
        db_path = 'instance/jewelry.db'
        
        # Remove the existing database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Старая база данных удалена.")
        
        # Create all tables with the new schema
        db.create_all()
        print("Новая база данных создана с обновленной схемой.")

if __name__ == '__main__':
    recreate_database() 