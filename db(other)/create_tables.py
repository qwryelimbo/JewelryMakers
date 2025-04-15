from app import app, db

def create_tables():
    with app.app_context():
        db.create_all()
        print("Таблицы базы данных успешно созданы.")

if __name__ == '__main__':
    create_tables() 