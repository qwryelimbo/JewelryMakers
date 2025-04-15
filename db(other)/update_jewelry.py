from app import app, db, Material, Jewelry
from datetime import datetime

def update_jewelry_catalog():
    with app.app_context():
        # Удаляем все существующие украшения
        Jewelry.query.delete()
        
        # Получаем материалы
        gold = Material.query.filter_by(name='Золото 585').first()
        silver = Material.query.filter_by(name='Серебро 925').first()
        platinum = Material.query.filter_by(name='Платина 950').first()
        
        # Создаем новые украшения
        jewelry_items = [
            {
                'name': 'Кольцо с бриллиантом',
                'description': 'Элегантное кольцо из белого золота с бриллиантом. Центральный камень огранки "принцесса" в классической оправе.',
                'category': 'Кольца',
                'price': 85000,
                'weight': 4.2,
                'image_path': 'jewelry/ring_diamond.jpg',
                'material': platinum,
                'stone_type': 'Бриллиант',
                'stone_carat': 0.75
            },
            {
                'name': 'Серьги с сапфирами',
                'description': 'Изысканные серьги из белого золота с сапфирами овальной огранки и бриллиантовым паве.',
                'category': 'Серьги',
                'price': 65000,
                'weight': 5.8,
                'image_path': 'jewelry/earrings_sapphire.jpg',
                'material': gold,
                'stone_type': 'Сапфир',
                'stone_carat': 1.2
            },
            {
                'name': 'Колье с изумрудом',
                'description': 'Роскошное колье из платины с центральным изумрудом грушевидной огранки и дорожкой из бриллиантов.',
                'category': 'Колье',
                'price': 175000,
                'weight': 12.3,
                'image_path': 'jewelry/necklace_emerald.jpg',
                'material': platinum,
                'stone_type': 'Изумруд',
                'stone_carat': 2.1
            },
            {
                'name': 'Браслет с рубинами',
                'description': 'Изящный браслет из белого золота с рубинами круглой огранки и бриллиантовым обрамлением.',
                'category': 'Браслеты',
                'price': 125000,
                'weight': 15.7,
                'image_path': 'jewelry/bracelet_ruby.jpg',
                'material': gold,
                'stone_type': 'Рубин',
                'stone_carat': 3.5
            },
            {
                'name': 'Браслет "Морская волна"',
                'description': 'Элегантный браслет из белого золота с аквамаринами и бриллиантами в волнообразном дизайне.',
                'category': 'Браслеты',
                'price': 95000,
                'weight': 13.5,
                'image_path': 'jewelry/wave_bracelet.jpg',
                'material': gold,
                'stone_type': 'Аквамарин',
                'stone_carat': 2.8
            },
            {
                'name': 'Серьги "Звездное сияние"',
                'description': 'Серьги из белого золота с бриллиантами в форме звезд с центральными сапфирами.',
                'category': 'Серьги',
                'price': 78000,
                'weight': 6.2,
                'image_path': 'jewelry/star_earrings.jpg',
                'material': gold,
                'stone_type': 'Сапфир',
                'stone_carat': 1.4
            },
            {
                'name': 'Подвеска "Солнечный свет"',
                'description': 'Подвеска из желтого золота с цитрином и бриллиантовым ореолом в форме солнца.',
                'category': 'Подвески',
                'price': 55000,
                'weight': 6.8,
                'image_path': 'jewelry/sun_pendant.jpg',
                'material': gold,
                'stone_type': 'Цитрин',
                'stone_carat': 1.8
            },
            {
                'name': 'Колье "Лесная сказка"',
                'description': 'Колье из белого золота с изумрудами и бриллиантами в природном дизайне.',
                'category': 'Колье',
                'price': 145000,
                'weight': 14.2,
                'image_path': 'jewelry/forest_necklace.jpg',
                'material': gold,
                'stone_type': 'Изумруд',
                'stone_carat': 2.5
            },
            {
                'name': 'Кольцо "Лунный свет"',
                'description': 'Кольцо из белого золота с лунным камнем и бриллиантовым обрамлением.',
                'category': 'Кольца',
                'price': 68000,
                'weight': 5.5,
                'image_path': 'jewelry/moon_ring.jpg',
                'material': gold,
                'stone_type': 'Лунный камень',
                'stone_carat': 1.6
            },
            {
                'name': 'Обручальное кольцо',
                'description': 'Классическое обручальное кольцо из белого золота с дорожкой из бриллиантов.',
                'category': 'Кольца',
                'price': 75000,
                'weight': 4.8,
                'image_path': 'jewelry/engagement_ring.jpg',
                'material': gold,
                'stone_type': 'Бриллиант',
                'stone_carat': 0.5
            }
        ]
        
        for item in jewelry_items:
            jewelry = Jewelry(
                name=item['name'],
                description=item['description'],
                category=item['category'],
                price=item['price'],
                weight=item['weight'],
                image_path=item['image_path'],
                material=item['material'],
                stone_type=item['stone_type'],
                stone_carat=item['stone_carat'],
                available=True
            )
            db.session.add(jewelry)
        
        try:
            db.session.commit()
            print("Каталог украшений успешно обновлен!")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при обновлении каталога: {str(e)}")

if __name__ == '__main__':
    update_jewelry_catalog() 