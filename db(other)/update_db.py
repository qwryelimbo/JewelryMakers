from app import app, db, User, Jewelry, Material, OrderStatus, Client
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

def create_admin():
    admin = User(
        username='admin',
        email='admin@jewelrystore.ru',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()

def create_master():
    master = User(
        username='master',
        email='master@jewelrystore.ru',
        password_hash=generate_password_hash('master123'),
        role='master'
    )
    db.session.add(master)
    db.session.commit()

def create_regular_user():
    user = User(
        username='user',
        email='user@jewelrystore.ru',
        password_hash=generate_password_hash('user123'),
        role='regular_client'
    )
    db.session.add(user)
    db.session.commit()

def create_regular_client():
    client = User(
        username='client',
        email='client@jewelrystore.ru',
        password_hash=generate_password_hash('client123'),
        role='regular_client'
    )
    db.session.add(client)
    db.session.commit()

def create_materials():
    materials = [
        {'id': 1, 'name': 'Золото 585', 'description': 'Сплав золота 585 пробы', 'current_price_per_gram': 5000},
        {'id': 2, 'name': 'Серебро 925', 'description': 'Сплав серебра 925 пробы', 'current_price_per_gram': 100},
        {'id': 3, 'name': 'Платина 950', 'description': 'Сплав платины 950 пробы', 'current_price_per_gram': 3000},
        {'id': 4, 'name': 'Палладий 950', 'description': 'Сплав палладия 950 пробы', 'current_price_per_gram': 2500},
        {'id': 5, 'name': 'Родий', 'description': 'Родиевое покрытие', 'current_price_per_gram': 2000},
        {'id': 6, 'name': 'Титан', 'description': 'Титановый сплав', 'current_price_per_gram': 800},
        {'id': 7, 'name': 'Вольфрам', 'description': 'Вольфрамовый сплав', 'current_price_per_gram': 600},
        {'id': 8, 'name': 'Керамика', 'description': 'Высокопрочная керамика', 'current_price_per_gram': 400},
        {'id': 9, 'name': 'Золото 750', 'description': 'Сплав золота 750 пробы', 'current_price_per_gram': 6000},
        {'id': 10, 'name': 'Серебро 960', 'description': 'Сплав серебра 960 пробы', 'current_price_per_gram': 150}
    ]
    
    for material_data in materials:
        material = Material(**material_data)
        db.session.add(material)
    db.session.commit()

def create_jewelry():
    jewelry_items = [
        {
            'name': 'Кольцо с бриллиантом',
            'description': 'Элегантное кольцо с бриллиантом в золотой оправе',
            'category': 'Кольца',
            'material_id': 1,
            'weight': 3.5,
            'price': 50000,
            'image_path': 'jewelry/ring_diamond.jpg',
            'stone_type': 'Бриллиант',
            'stone_carat': 0.5,
            'available': True
        },
        {
            'name': 'Серьги с сапфиром',
            'description': 'Изящные серьги с сапфирами в серебряной оправе',
            'category': 'Серьги',
            'material_id': 2,
            'weight': 2.8,
            'price': 15000,
            'image_path': 'jewelry/earrings_sapphire.jpg',
            'stone_type': 'Сапфир',
            'stone_carat': 0.3,
            'available': True
        },
        {
            'name': 'Ожерелье с изумрудом',
            'description': 'Роскошное ожерелье с изумрудом в золотой оправе',
            'category': 'Ожерелья',
            'material_id': 1,
            'weight': 5.2,
            'price': 75000,
            'image_path': 'jewelry/necklace_emerald.jpg',
            'stone_type': 'Изумруд',
            'stone_carat': 0.8,
            'available': True
        },
        {
            'name': 'Браслет с рубином',
            'description': 'Элегантный браслет с рубинами в золотой оправе',
            'category': 'Браслеты',
            'material_id': 1,
            'weight': 4.0,
            'price': 60000,
            'image_path': 'jewelry/bracelet_ruby.jpg',
            'stone_type': 'Рубин',
            'stone_carat': 0.6,
            'available': True
        },
        {
            'name': 'Браслет Волна',
            'description': 'Современный браслет с волнообразным дизайном',
            'category': 'Браслеты',
            'material_id': 3,
            'weight': 3.2,
            'price': 45000,
            'image_path': 'jewelry/wave_bracelet.jpg',
            'available': True
        },
        {
            'name': 'Серьги Звезда',
            'description': 'Стильные серьги в форме звезды',
            'category': 'Серьги',
            'material_id': 4,
            'weight': 2.5,
            'price': 35000,
            'image_path': 'jewelry/star_earrings.jpg',
            'available': True
        },
        {
            'name': 'Подвеска Солнце',
            'description': 'Яркая подвеска в форме солнца',
            'category': 'Подвески',
            'material_id': 5,
            'weight': 1.8,
            'price': 28000,
            'image_path': 'jewelry/sun_pendant.jpg',
            'available': True
        },
        {
            'name': 'Ожерелье Лес',
            'description': 'Ожерелье с природным дизайном',
            'category': 'Ожерелья',
            'material_id': 6,
            'weight': 3.0,
            'price': 22000,
            'image_path': 'jewelry/forest_necklace.jpg',
            'available': True
        },
        {
            'name': 'Кольцо Луна',
            'description': 'Элегантное кольцо с лунным дизайном',
            'category': 'Кольца',
            'material_id': 7,
            'weight': 2.2,
            'price': 18000,
            'image_path': 'jewelry/moon_ring.jpg',
            'available': True
        },
        {
            'name': 'Обручальное кольцо',
            'description': 'Классическое обручальное кольцо',
            'category': 'Кольца',
            'material_id': 8,
            'weight': 2.0,
            'price': 15000,
            'image_path': 'jewelry/engagement_ring.jpg',
            'available': True
        }
    ]
    
    for jewelry_data in jewelry_items:
        jewelry = Jewelry(**jewelry_data)
        db.session.add(jewelry)
    db.session.commit()

def create_order_statuses():
    statuses = ['В ожидании', 'В обработке', 'В производстве', 'Готов к выдаче', 'Завершён', 'Отменён']
    for status in statuses:
        if not OrderStatus.query.filter_by(name=status).first():
            order_status = OrderStatus(name=status)
            db.session.add(order_status)
    db.session.commit()

def create_test_clients():
    # Создаем тестовых пользователей и клиентов
    test_data = [
        {
            'user': {
                'username': 'client1',
                'email': 'client1@jewelrystore.ru',
                'password': 'client123',
                'role': 'client'
            },
            'client': {
                'last_name': 'Иванов',
                'first_name': 'Иван',
                'middle_name': 'Иванович',
                'phone_number': '+7 (999) 123-45-67',
                'birth_date': datetime(1990, 1, 1),
                'is_regular': True
            }
        },
        {
            'user': {
                'username': 'client2',
                'email': 'client2@jewelrystore.ru',
                'password': 'client123',
                'role': 'client'
            },
            'client': {
                'last_name': 'Петров',
                'first_name': 'Петр',
                'middle_name': 'Петрович',
                'phone_number': '+7 (999) 765-43-21',
                'birth_date': datetime(1995, 5, 15),
                'is_regular': False
            }
        }
    ]
    
    for data in test_data:
        # Создаем пользователя
        user = User(
            username=data['user']['username'],
            email=data['user']['email'],
            password_hash=generate_password_hash(data['user']['password']),
            role=data['user']['role']
        )
        db.session.add(user)
        db.session.flush()  # Получаем ID пользователя
        
        # Создаем клиента
        client = Client(
            user_id=user.id,
            last_name=data['client']['last_name'],
            first_name=data['client']['first_name'],
            middle_name=data['client']['middle_name'],
            phone_number=data['client']['phone_number'],
            birth_date=data['client']['birth_date'],
            is_regular=data['client']['is_regular']
        )
        db.session.add(client)
    
    db.session.commit()

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        create_materials()
        create_order_statuses()
        create_admin()
        create_master()
        create_regular_user()
        create_regular_client()
        create_test_clients()  # Добавляем создание тестовых клиентов
        create_jewelry()

if __name__ == '__main__':
    init_db()
    print("База данных успешно обновлена!") 