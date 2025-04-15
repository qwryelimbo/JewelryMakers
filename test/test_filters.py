import pytest
from app import app, db, Jewelry, Material
from flask import url_for

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jewelrystore.db'  # Используем основную БД
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_filter_by_material(client):
    """Test filtering jewelry by material"""
    # Get the gold material ID from the database
    with app.app_context():
        gold = Material.query.filter_by(name='Золото 585').first()
        gold_id = gold.id
    
    response = client.get(f'/catalog?material={gold_id}')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    assert 'Кольцо с бриллиантом' in data
    assert 'Ожерелье с изумрудом' in data
    assert 'Браслет с рубином' in data
    assert 'Серьги с сапфиром' not in data

def test_filter_by_category(client):
    """Test filtering jewelry by category"""
    response = client.get('/catalog?category=Кольца')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    assert 'Кольцо с бриллиантом' in data
    assert 'Кольцо Луна' in data
    assert 'Серьги с сапфиром' not in data
    assert 'Ожерелье с изумрудом' not in data

def test_filter_by_price_range(client):
    """Test filtering jewelry by price range"""
    response = client.get('/catalog?price_min=15000&price_max=35000')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    assert 'Серьги с сапфиром' in data
    assert 'Обручальное кольцо' in data
    assert 'Серьги Звезда' in data
    assert 'Кольцо с бриллиантом' not in data
    assert 'Ожерелье с изумрудом' not in data
