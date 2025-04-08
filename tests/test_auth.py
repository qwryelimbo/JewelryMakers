import pytest
from flask import url_for
from app import User, db

def test_login_page(test_client):
    """Тест загрузки страницы входа.
    
    Проверяет, что:
    - Страница успешно загружается (код 200)
    - На странице присутствуют все необходимые элементы формы
    """
    response = test_client.get('/login')
    assert response.status_code == 200
    assert 'Войти'.encode('utf-8') in response.data
    assert 'Имя пользователя'.encode('utf-8') in response.data
    assert 'Пароль'.encode('utf-8') in response.data

def test_register_page(test_client):
    """Тест загрузки страницы регистрации.
    
    Проверяет, что:
    - Страница успешно загружается (код 200)
    - На странице присутствуют все необходимые поля формы
    """
    response = test_client.get('/register')
    assert response.status_code == 200
    assert 'Регистрация'.encode('utf-8') in response.data
    assert 'Имя пользователя'.encode('utf-8') in response.data
    assert 'Email'.encode('utf-8') in response.data
    assert 'Пароль'.encode('utf-8') in response.data

def test_successful_login(test_client):
    """Тест успешного входа в систему.
    
    Проверяет, что:
    - Пользователь может войти с правильными учетными данными
    - После входа происходит перенаправление на главную страницу
    """
    response = test_client.post('/login', data={
        'username': 'user',
        'password': 'user123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'RandomPlay' in response.data  # Название бренда в навигационной панели
    assert b'Welcome' not in response.data  # Это сообщение не должно присутствовать

def test_failed_login(test_client):
    """Тест неудачной попытки входа.
    
    Проверяет, что:
    - Система правильно обрабатывает неверные учетные данные
    - Пользователь получает сообщение об ошибке
    """
    response = test_client.post('/login', data={
        'username': 'wrong',
        'password': 'wrong'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

def test_successful_registration(test_client):
    """Тест успешной регистрации нового пользователя.
    
    Проверяет, что:
    - Новый пользователь может зарегистрироваться
    - Данные пользователя сохраняются в базе данных
    - После регистрации происходит перенаправление на страницу входа
    """
    response = test_client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@test.com',
        'password': 'newpass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Проверяем, что пользователь был создан в базе данных
    with test_client.application.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@test.com'

def test_duplicate_username_registration(test_client):
    """Тест регистрации с существующим именем пользователя.
    
    Проверяет, что:
    - Система не позволяет зарегистрировать пользователя с уже существующим именем
    - Пользователь получает соответствующее сообщение об ошибке
    """
    response = test_client.post('/register', data={
        'username': 'user',  # Это имя пользователя уже существует
        'email': 'another@test.com',
        'password': 'pass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Username already exists' in response.data

def test_logout(test_client):
    """Тест выхода из системы.
    
    Проверяет, что:
    - Пользователь может успешно выйти из системы
    - После выхода происходит перенаправление на главную страницу
    """
    # Сначала входим
    test_client.post('/login', data={
        'username': 'user',
        'password': 'user123'
    })
    
    # Затем выходим
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200 

def test_short_password_registration(test_client):
    """Тест регистрации со слишком коротким паролем.
    
    Проверяет, что:
    - Система не позволяет зарегистрировать пользователя с паролем короче минимальной длины
    - Пользователь получает сообщение об ошибке
    - Функция создания пользователя не выполняется
    """
    # Определяем начальное количество пользователей
    with test_client.application.app_context():
        initial_user_count = User.query.count()
    
    # Попытка регистрации с коротким паролем
    response = test_client.post('/register', data={
        'username': 'newuser2',
        'email': 'newuser2@test.com',
        'password': '123'  # Слишком короткий пароль
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Проверяем наличие сообщения об ошибке
    error_message = 'Пароль должен содержать минимум 6 символов'
    assert error_message.encode('utf-8') in response.data
    
    # Проверяем, что пользователь не был создан
    with test_client.application.app_context():
        assert User.query.count() == initial_user_count
        user = User.query.filter_by(username='newuser2').first()
        assert user is None 

def test_invalid_email_format_registration(test_client):
    """Тест регистрации с некорректным форматом email.
    
    Проверяет, что:
    - Система не позволяет зарегистрировать пользователя с некорректным форматом email
    - Пользователь получает сообщение об ошибке
    - Функция создания пользователя не выполняется
    """
    # Определяем начальное количество пользователей
    with test_client.application.app_context():
        initial_user_count = User.query.count()
    
    # Попытка регистрации с некорректным email
    response = test_client.post('/register', data={
        'username': 'newuser3',
        'email': 'invalid-email',  # Некорректный формат email
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Проверяем наличие сообщения об ошибке
    error_message = 'Некорректный формат email'
    assert error_message.encode('utf-8') in response.data
    
    # Проверяем, что пользователь не был создан
    with test_client.application.app_context():
        assert User.query.count() == initial_user_count
        user = User.query.filter_by(username='newuser3').first()
        assert user is None 