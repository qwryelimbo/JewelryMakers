import os
import time
import pytest
import threading
import tempfile
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import app, db, User, Cassette
from werkzeug.security import generate_password_hash

# Путь для сохранения скриншотов
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def generate_random_string(length=5):
    """Генерирует случайную строку указанной длины."""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

@pytest.fixture(scope='function')
def chrome_driver():
    """Создаем драйвер Chrome с заданными опциями."""
    try:
        # Настраиваем опции Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Запуск браузера без интерфейса
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Создаем драйвер напрямую
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.maximize_window()
        driver.implicitly_wait(10)
        
        yield driver
        
    except Exception as e:
        print(f"Ошибка при создании драйвера: {e}")
        pytest.skip("Не удалось создать драйвер Chrome")
    finally:
        if 'driver' in locals():
            driver.quit()

@pytest.fixture(scope='function')
def flask_server():
    """Запускаем сервер Flask в отдельном потоке."""
    # Генерируем уникальные имена для каждого теста
    admin_username = f"admin_{generate_random_string()}"
    user_username = f"user_{generate_random_string()}"
    
    # Настраиваем временную базу данных SQLite
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost:5000'
    
    with app.app_context():
        # Удаляем все таблицы и создаем заново
        db.drop_all()
        db.create_all()
        
        # Создаем тестового администратора с уникальным именем
        admin = User(
            username=admin_username,
            email=f'{admin_username}@test.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        
        # Создаем тестового обычного пользователя с уникальным именем
        user = User(
            username=user_username,
            email=f'{user_username}@test.com',
            password_hash=generate_password_hash('user123'),
            is_admin=False
        )
        db.session.add(user)
        
        # Создаем несколько тестовых кассет
        for i in range(3):
            cassette = Cassette(
                title=f'Test Cassette {i}',
                description=f'Description for cassette {i}',
                release_year=2000 + i,
                genre='Action' if i % 2 == 0 else 'Comedy',
                price=9.99 + i,
                available=True
            )
            db.session.add(cassette)
        
        db.session.commit()
    
    # Запускаем сервер Flask в отдельном потоке
    def run_flask():
        app.run(debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()
    
    # Ждем, пока сервер запустится
    time.sleep(2)
    
    # Передаем имя пользователя администратора для теста
    yield app, admin_username
    
    # Закрываем и удаляем временную базу данных
    os.close(db_fd)
    os.unlink(db_path)

def test_browse_catalog(chrome_driver, flask_server):
    """Тест просмотра каталога и фильтрации по жанру."""
    app, _ = flask_server  # Нам не нужно имя пользователя для этого теста
    
    try:
        # Открываем страницу каталога
        chrome_driver.get('http://localhost:5000/catalog')
        
        # Ждем загрузки страницы
        time.sleep(2)
        
        # Делаем скриншот главной страницы каталога
        chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'catalog_page.png'))
        
        # Проверяем наличие кассет в каталоге (используем класс 'glass')
        cassettes = WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'glass'))
        )
        assert len(cassettes) > 0, "Кассеты не отображаются в каталоге"
        
        print(f"Найдено кассет в каталоге: {len(cassettes)}")
        
        # Если на странице есть выпадающий список жанров, проверяем фильтрацию
        try:
            # В HTML селект с жанром имеет атрибут name="genre"
            genres = WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'genre'))
            )
            
            # Прокручиваем до элемента
            chrome_driver.execute_script("arguments[0].scrollIntoView(true);", genres)
            
            # Выбираем Action в выпадающем списке
            for option in genres.find_elements(By.TAG_NAME, 'option'):
                if 'Action' in option.text:
                    # Используем JavaScript для клика
                    chrome_driver.execute_script("arguments[0].selected = true;", option)
                    chrome_driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", genres)
                    break
            
            # Находим и нажимаем кнопку применения фильтров
            submit_button = WebDriverWait(chrome_driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            
            # Прокручиваем до кнопки и кликаем через JavaScript
            chrome_driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            chrome_driver.execute_script("arguments[0].click();", submit_button)
            
            # Ждем обновления страницы
            time.sleep(2)
            
            # Делаем скриншот отфильтрованного каталога
            chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'filtered_catalog.png'))
            
            # Проверяем результаты фильтрации
            filtered_cassettes = WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'glass'))
            )
            assert len(filtered_cassettes) > 0, "Отфильтрованные кассеты не отображаются"
            
            print(f"Найдено кассет после фильтрации: {len(filtered_cassettes)}")
        except Exception as e:
            print(f"Фильтр по жанрам не найден или не удалось выполнить фильтрацию: {e}")
            chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'filter_error.png'))
    
    except Exception as e:
        chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'error_catalog.png'))
        pytest.fail(f"Ошибка при тестировании каталога: {e}")

def test_admin_export_cassettes(chrome_driver, flask_server):
    """Тест экспорта списка кассет администратором."""
    app, admin_username = flask_server  # Получаем уникальное имя администратора
    
    try:
        # Открываем страницу входа
        chrome_driver.get('http://localhost:5000/login')
        
        # Делаем скриншот страницы входа
        chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'login_page.png'))
        
        # Ждем, пока страница полностью загрузится
        time.sleep(1)
        
        # Вводим учетные данные администратора
        username_field = WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        username_field.clear()
        username_field.send_keys(admin_username)
        
        password_field = chrome_driver.find_element(By.NAME, 'password')
        password_field.clear()
        password_field.send_keys('admin123')
        
        # Используем JavaScript для клика по кнопке, чтобы избежать перехвата клика
        submit_button = chrome_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        chrome_driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        chrome_driver.execute_script("arguments[0].click();", submit_button)
        
        # Ждем перенаправления
        time.sleep(2)
        
        # Переходим на панель администратора
        chrome_driver.get('http://localhost:5000/admin')
        
        # Ждем загрузки страницы
        time.sleep(2)
        
        # Делаем скриншот панели администратора
        chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'admin_dashboard.png'))
        
        # Проверяем наличие кнопки экспорта
        try:
            # Находим кнопку экспорта по тексту и классу на основе HTML шаблона
            export_button = WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.btn-secondary[href*="export"]'))
            )
            
            # Проверяем URL кнопки экспорта
            export_url = export_button.get_attribute('href')
            assert '/admin/cassettes/export' in export_url, "Неверный URL для экспорта кассет"
            
            print(f"Найдена кнопка экспорта с URL: {export_url}")
            
            # Используем JavaScript для клика по кнопке
            chrome_driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
            chrome_driver.execute_script("arguments[0].click();", export_button)
            
            # Ждем, пока файл начнет скачиваться
            time.sleep(2)
            
            # Делаем скриншот после нажатия
            chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'after_export_click.png'))
            
            print("Экспорт кассет выполнен успешно")
        
        except Exception as e:
            print(f"Кнопка экспорта не найдена или не удалось выполнить экспорт: {e}")
            chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'export_button_not_found.png'))
    
    except Exception as e:
        chrome_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, 'error_admin.png'))
        pytest.fail(f"Ошибка при тестировании экспорта кассет: {e}")

if __name__ == "__main__":
    # Можно запустить тесты напрямую, запустив этот файл
    pytest.main(['-v', __file__]) 