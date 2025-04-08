import pytest
from app import Cassette, db

def test_catalog_page(test_client):
    """Тест загрузки страницы каталога.
    
    Проверяет, что:
    - Страница каталога успешно загружается (код 200)
    - На странице присутствует заголовок "Каталог"
    """
    response = test_client.get('/catalog')
    assert response.status_code == 200
    assert 'Каталог'.encode('utf-8') in response.data

def test_catalog_filtering(test_client, test_cassette):
    """Тест фильтрации каталога.
    
    Проверяет, что:
    - Фильтрация по жанру работает корректно
    - Фильтрация по цене работает корректно
    - Фильтрация по году выпуска работает корректно
    - В результатах фильтрации показываются только подходящие кассеты
    """
    # Добавляем еще одну кассету с другими свойствами
    with test_client.application.app_context():
        another_cassette = Cassette(
            title='Another Cassette',
            description='Another Description',
            release_year=2015,
            genre='Jazz',
            price=20.99,
            available=True
        )
        db.session.add(another_cassette)
        db.session.commit()
    
    # Тест фильтра по жанру
    response = test_client.get('/catalog?genre=Rock')
    assert response.status_code == 200
    assert b'Test Cassette' in response.data
    assert b'Another Cassette' not in response.data
    
    # Тест фильтра по цене
    response = test_client.get('/catalog?min_price=10&max_price=11')
    assert response.status_code == 200
    assert b'Test Cassette' in response.data
    assert b'Another Cassette' not in response.data
    
    # Тест фильтра по году
    response = test_client.get('/catalog?min_year=2019&max_year=2021')
    assert response.status_code == 200
    assert b'Test Cassette' in response.data
    assert b'Another Cassette' not in response.data

def test_product_details(test_client, test_cassette):
    """Тест страницы деталей продукта.
    
    Проверяет, что:
    - Страница деталей кассеты успешно загружается
    - На странице отображается вся информация о кассете
    """
    response = test_client.get(f'/cassette/{test_cassette.id}')
    assert response.status_code == 200
    assert b'Test Cassette' in response.data
    assert b'Test Description' in response.data
    assert b'Rock' in response.data
    assert b'10.99' in response.data

def test_admin_add_cassette(test_client, admin_user):
    """Тест добавления новой кассеты администратором.
    
    Проверяет, что:
    - Администратор может добавить новую кассету
    - Данные кассеты корректно сохраняются в базе данных
    """
    # Сначала входим как администратор
    test_client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    
    # Добавляем новую кассету
    response = test_client.post('/admin/cassette/add', data={
        'title': 'New Cassette',
        'description': 'New Description',
        'release_year': 2021,
        'genre': 'Jazz',
        'price': 15.99
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Проверяем, что кассета была создана
    with test_client.application.app_context():
        cassette = Cassette.query.filter_by(title='New Cassette').first()
        assert cassette is not None
        assert cassette.genre == 'Jazz'
        assert cassette.price == 15.99

def test_admin_edit_cassette(test_client, admin_user, test_cassette):
    """Тест редактирования кассеты администратором.
    
    Проверяет, что:
    - Администратор может отредактировать существующую кассету
    - Изменения корректно сохраняются в базе данных
    """
    # Сначала входим как администратор
    test_client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    
    # Редактируем кассету
    response = test_client.post(f'/admin/cassette/edit/{test_cassette.id}', data={
        'title': 'Updated Cassette',
        'description': 'Updated Description',
        'release_year': 2022,
        'genre': 'Blues',
        'price': 12.99
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Проверяем изменения
    with test_client.application.app_context():
        updated_cassette = db.session.get(Cassette, test_cassette.id)
        assert updated_cassette.title == 'Updated Cassette'
        assert updated_cassette.genre == 'Blues'
        assert updated_cassette.price == 12.99

def test_admin_delete_cassette(test_client, admin_user, test_cassette):
    """Тест удаления кассеты администратором.
    
    Проверяет, что:
    - Администратор может удалить кассету
    - Кассета успешно удаляется из базы данных
    """
    # Сначала входим как администратор
    test_client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    
    # Удаляем кассету
    response = test_client.get(f'/admin/cassette/delete/{test_cassette.id}', follow_redirects=True)
    assert response.status_code == 200
    
    # Проверяем, что кассета была удалена
    with test_client.application.app_context():
        deleted_cassette = db.session.get(Cassette, test_cassette.id)
        assert deleted_cassette is None

def test_regular_user_cannot_access_admin(test_client, regular_user):
    """Тест ограничения доступа к админ-панели.
    
    Проверяет, что:
    - Обычный пользователь не может получить доступ к админ-панели
    - При попытке доступа происходит перенаправление на главную страницу
    """
    # Входим как обычный пользователь
    test_client.post('/login', data={
        'username': 'user',
        'password': 'user123'
    })
    
    # Пытаемся получить доступ к админ-панели
    response = test_client.get('/admin', follow_redirects=True)
    assert response.status_code == 200
    assert b'RandomPlay' in response.data  # Должно быть перенаправление на главную страницу 

def test_export_cassettes(test_client, admin_user):
    """Тест экспорта кассет в CSV файл.
    
    Проверяет, что:
    - Администратор может экспортировать список кассет в CSV файл
    - Файл содержит корректные данные
    """
    # Сначала входим как администратор
    test_client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    
    # Экспортируем кассеты
    response = test_client.get('/admin/cassettes/export')
    assert response.status_code == 200
    
    # Проверяем заголовки ответа
    assert 'text/csv' in response.content_type
    assert 'attachment; filename=cassettes_' in response.headers.get('Content-Disposition')
    
    # Проверяем содержимое CSV файла
    content = response.data.decode('utf-8-sig')
    assert 'ID;Название;Описание;Год выпуска;Жанр;Цена;Доступность' in content
    
    # Проверяем, что данные тестовой кассеты есть в файле
    with test_client.application.app_context():
        test_cassette = db.session.query(Cassette).first()
        assert str(test_cassette.id) in content
        assert test_cassette.title in content 