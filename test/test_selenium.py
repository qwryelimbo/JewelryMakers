import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
import sys
import os
import time

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db, Material, Jewelry
import chromedriver_autoinstaller
import threading
from werkzeug.serving import make_server

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 5000, app)

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

@pytest.fixture(scope="module")
def driver():
    # Автоматическая установка и настройка ChromeDriver
    chromedriver_autoinstaller.install()
    
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Закомментируем эту строку
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()  # Разворачиваем окно на весь экран
    driver.implicitly_wait(10)
    yield driver
    time.sleep(2)  # Пауза перед закрытием браузера
    driver.quit()

@pytest.fixture(scope="module")
def test_app():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jewelrystore.db'  # Используем основную БД
    return app

@pytest.fixture(scope="module")
def test_client(test_app):
    with test_app.test_client() as client:
        with test_app.app_context():
            # Удаляем создание и очистку БД, так как используем существующую
            yield client

@pytest.fixture(scope="module")
def server(test_app, test_client):
    """Start test server in a separate thread"""
    server = ServerThread(test_app)
    server.start()
    yield server
    server.shutdown()
    server.join()

def test_catalog_navigation(driver, server):
    """Тест перехода в каталог"""
    driver.get('http://localhost:5000')
    time.sleep(1)  # Пауза для наглядности
    catalog_link = driver.find_element(By.LINK_TEXT, 'Каталог')
    catalog_link.click()
    time.sleep(1)  # Пауза для наглядности
    
    # Проверяем URL
    assert driver.current_url == 'http://localhost:5000/catalog'
    # Проверяем наличие фильтров
    assert driver.find_element(By.ID, 'category').is_displayed()
    assert driver.find_element(By.ID, 'material').is_displayed()
    time.sleep(1)  # Пауза в конце теста

def test_category_filter(driver, server):
    """Тест фильтрации по категории"""
    driver.get('http://localhost:5000/catalog')
    time.sleep(1)  # Пауза для наглядности
    
    # Выбираем категорию "Кольца"
    category_select = Select(driver.find_element(By.ID, 'category'))
    category_select.select_by_visible_text('Кольца')
    time.sleep(1)  # Пауза для наглядности
    
    # Нажимаем кнопку применения фильтров
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(1)  # Пауза для наглядности
    
    # Ждем обновления результатов
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'glass-card'))
    )
    
    # Проверяем результаты
    cards = driver.find_elements(By.CLASS_NAME, 'glass-card')
    card_titles = [card.find_element(By.CLASS_NAME, 'card-title').text for card in cards]
    
    assert 'Кольцо с бриллиантом' in card_titles
    assert 'Кольцо Луна' in card_titles
    assert 'Серьги с сапфиром' not in card_titles
    time.sleep(1)  # Пауза в конце теста

def test_material_filter(driver, server):
    """Тест фильтрации по материалу"""
    driver.get('http://localhost:5000/catalog')
    time.sleep(1)  # Пауза для наглядности
    
    # Выбираем материал "Золото 585"
    material_select = Select(driver.find_element(By.ID, 'material'))
    material_select.select_by_visible_text('Золото 585')
    time.sleep(1)  # Пауза для наглядности
    
    # Нажимаем кнопку применения фильтров
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(1)  # Пауза для наглядности
    
    # Ждем обновления результатов
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'glass-card'))
    )
    
    # Проверяем результаты
    cards = driver.find_elements(By.CLASS_NAME, 'glass-card')
    card_titles = [card.find_element(By.CLASS_NAME, 'card-title').text for card in cards]
    
    assert 'Кольцо с бриллиантом' in card_titles
    assert 'Ожерелье с изумрудом' in card_titles
    assert 'Браслет с рубином' in card_titles
    assert 'Серьги с сапфиром' not in card_titles
    time.sleep(1)  # Пауза в конце теста

def test_price_range_filter(driver, server):
    """Тест фильтрации по диапазону цен"""
    driver.get('http://localhost:5000/catalog')
    time.sleep(1)  # Пауза для наглядности
    
    # Устанавливаем диапазон цен
    min_price = driver.find_element(By.ID, 'price_min')
    max_price = driver.find_element(By.ID, 'price_max')
    
    min_price.clear()
    min_price.send_keys('50000')
    time.sleep(0.5)  # Пауза для наглядности
    max_price.clear()
    max_price.send_keys('75000')
    time.sleep(1)  # Пауза для наглядности
    
    # Нажимаем кнопку применения фильтров
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(1)  # Пауза для наглядности
    
    # Ждем обновления результатов
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'glass-card'))
    )
    
    # Проверяем результаты
    cards = driver.find_elements(By.CLASS_NAME, 'glass-card')
    card_titles = [card.find_element(By.CLASS_NAME, 'card-title').text for card in cards]
    
    assert 'Кольцо с бриллиантом' in card_titles
    assert 'Ожерелье с изумрудом' in card_titles
    assert 'Браслет с рубином' in card_titles
    assert 'Серьги с сапфиром' not in card_titles
    time.sleep(1)  # Пауза в конце теста 