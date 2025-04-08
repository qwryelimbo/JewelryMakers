# RandomPlay - Video Cassette Rental System

A web application for managing a video cassette rental service, built with Python Flask and SQLite.

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
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('your-password')
    db.session.add(admin)
    db.session.commit()
```

6. Run the application:
```bash
python app.py
```

7. Open your browser and navigate to `http://localhost:5000`

## Usage

### Regular Users
- Browse the catalog of available cassettes
- Search for specific titles
- View detailed information about each cassette
- Register and login to rent cassettes

### Administrators
- Access the admin panel at `/admin`
- Add, edit, and delete cassettes
- View all cassettes in the system
- Manage user accounts and rentals

## Security Notes

- Change the `SECRET_KEY` in `app.py` before deploying to production
- Use environment variables for sensitive information
- Implement proper password hashing (already included)
- Add rate limiting for login attempts
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 