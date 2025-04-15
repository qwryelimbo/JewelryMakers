# JewelryMakers - Ювелирная мастерская

Система управления ювелирной мастерской с возможностью онлайн-заказов и администрирования.

## Features

- User authentication (login/register)
- Admin panel for managing cassettes
- Catalog browsing with search functionality
- Dark theme with glassmorphism design
- Responsive layout

## Database Structure

The application uses SQLite with the following main tables:

- Users: Store user information and authentication details
- Cassettes: Store video cassette information
- Defects: Track cassette defects and repairs
- Rentals: Record cassette rentals and returns

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/randomplay.git
cd randomplay
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

5. Create an admin user:
```python
from app import app, db, User
with app.app_context():
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('your-password')
    db.session.add(admin)
    db.session.commit()
```