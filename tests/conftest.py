import os
import pytest
from app import app, db, User, Cassette
from werkzeug.security import generate_password_hash
from flask import Flask

@pytest.fixture
def test_app():
    """Create and configure a test Flask application."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the app."""
    with test_app.test_client() as testing_client:
        with test_app.app_context():
            # Drop all tables first to ensure a clean state
            db.drop_all()
            # Create all tables
            db.create_all()
            
            # Create test admin user
            admin = User(
                username='admin',
                email='admin@test.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            
            # Create test regular user
            user = User(
                username='user',
                email='user@test.com',
                password_hash=generate_password_hash('user123'),
                is_admin=False
            )
            db.session.add(user)
            
            # Create test cassette
            cassette = Cassette(
                title='Test Cassette',
                description='Test Description',
                release_year=2020,
                genre='Rock',
                price=10.99,
                available=True
            )
            db.session.add(cassette)
            
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise
        
        yield testing_client
        
        # Cleanup after each test
        with test_app.app_context():
            db.session.remove()
            db.drop_all()

@pytest.fixture
def test_runner(test_app):
    """Create a test CLI runner."""
    return test_app.test_cli_runner()

@pytest.fixture
def admin_user(test_app):
    """Return the admin user."""
    with test_app.app_context():
        return User.query.filter_by(username='admin').first()

@pytest.fixture
def regular_user(test_app):
    """Return the regular user."""
    with test_app.app_context():
        return User.query.filter_by(username='user').first()

@pytest.fixture
def test_cassette(test_app):
    """Return the test cassette."""
    with test_app.app_context():
        return Cassette.query.filter_by(title='Test Cassette').first() 