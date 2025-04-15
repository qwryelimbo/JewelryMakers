from app import app, db, User, Client, Material, Jewelry, OrderStatus
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create admin user
        admin = User(
            username='admin',
            email='admin@jewelrystore.ru',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            avatar='avatars/admin.jpg',
            date_joined=datetime.utcnow()
        )
        db.session.add(admin)

        # Create sample client
        client = Client(
            user_id=1,
            last_name='Иванов',
            first_name='Иван',
            middle_name='Иванович',
            phone_number='+7 (999) 123-45-67',
            birth_date=datetime(1990, 1, 1),
            is_regular=True,
            orders_count=5,
            total_spent=150000.0
        )
        db.session.add(client)

        # Create materials
        materials = [
            Material(name='Золото 585', inventory_grams=1000),
            Material(name='Серебро 925', inventory_grams=2000),
            Material(name='Платина', inventory_grams=500),
            Material(name='Белое золото', inventory_grams=800),
            Material(name='Розовое золото', inventory_grams=600)
        ]
        
        for material in materials:
            db.session.add(material)
        
        # Create jewelry items
        jewelry_items = [
            {
                'name': 'Кольцо с бриллиантом',
                'description': 'Элегантное кольцо из белого золота с бриллиантом',
                'material': 'Белое золото',
                'category': 'Кольца',
                'price': 50000.0,
                'weight': 5.0,
                'stone_type': 'Бриллиант',
                'stone_carat': 0.5,
                'image_path': 'jewelry/ring_diamond.jpg'
            },
            {
                'name': 'Серьги с сапфирами',
                'description': 'Изысканные серьги из золота с сапфирами',
                'material': 'Золото 585',
                'category': 'Серьги',
                'price': 35000.0,
                'weight': 3.5,
                'stone_type': 'Сапфир',
                'stone_carat': 0.3,
                'image_path': 'jewelry/earrings_sapphire.jpg'
            },
            {
                'name': 'Колье с изумрудами',
                'description': 'Роскошное колье из платины с изумрудами',
                'material': 'Платина',
                'category': 'Колье',
                'price': 120000.0,
                'weight': 15.0,
                'stone_type': 'Изумруд',
                'stone_carat': 1.0,
                'image_path': 'jewelry/necklace_emerald.jpg'
            },
            {
                'name': 'Браслет с рубинами',
                'description': 'Изящный браслет из розового золота с рубинами',
                'material': 'Розовое золото',
                'category': 'Браслеты',
                'price': 75000.0,
                'weight': 8.0,
                'stone_type': 'Рубин',
                'stone_carat': 0.8,
                'image_path': 'jewelry/bracelet_ruby.jpg'
            }
        ]
        
        for item_data in jewelry_items:
            jewelry = Jewelry(**item_data)
            db.session.add(jewelry)
        
        # Create order statuses
        statuses = [
            OrderStatus(name='Новый'),
            OrderStatus(name='В обработке'),
            OrderStatus(name='Изготавливается'),
            OrderStatus(name='Готов к выдаче'),
            OrderStatus(name='Завершён'),
            OrderStatus(name='Отменён')
        ]
        
        for status in statuses:
            db.session.add(status)
        
        # Commit all changes
        db.session.commit()

if __name__ == '__main__':
    seed_database()
    print("Database has been seeded successfully!") 