from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import os
from werkzeug.utils import secure_filename
import csv
from io import StringIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///randomplay.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/cassettes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    rentals = db.relationship('Rental', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Cassette(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    release_year = db.Column(db.Integer)
    genre = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)
    image_path = db.Column(db.String(200), default='cassettes/default.jpg')
    defects = db.relationship('Defect', backref='cassette', lazy=True)
    rentals = db.relationship('Rental', backref='cassette', lazy=True)

class Defect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cassette_id = db.Column(db.Integer, db.ForeignKey('cassette.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    is_fixed = db.Column(db.Boolean, default=False)

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cassette_id = db.Column(db.Integer, db.ForeignKey('cassette.id'), nullable=False)
    rental_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    is_returned = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def save_image(file, cassette_id):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{cassette_id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return f"cassettes/{filename}"
    return None

# Routes
@app.route('/')
def index():
    all_cassettes = Cassette.query.all()
    random_cassettes = random.sample(all_cassettes, min(4, len(all_cassettes)))
    return render_template('index.html', random_cassettes=random_cassettes)

@app.route('/catalog')
def catalog():
    # Start with base query
    query = Cassette.query

    # Apply genre filter
    genre = request.args.get('genre')
    if genre:
        query = query.filter(Cassette.genre == genre)

    # Apply price range filter
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    if min_price:
        query = query.filter(Cassette.price >= float(min_price))
    if max_price:
        query = query.filter(Cassette.price <= float(max_price))

    # Apply year range filter
    min_year = request.args.get('min_year')
    max_year = request.args.get('max_year')
    if min_year:
        query = query.filter(Cassette.release_year >= int(min_year))
    if max_year:
        query = query.filter(Cassette.release_year <= int(max_year))

    # Apply availability filter
    if request.args.get('available_only'):
        query = query.filter(Cassette.available == True)

    # Execute query
    cassettes = query.all()
    
    # Get unique genres for filter dropdown
    all_cassettes = Cassette.query.all()
    genres = sorted(list(set(cassette.genre for cassette in all_cassettes)))
    
    # Pass selected genre to template for maintaining filter state
    selected_genre = genre if genre else ''
    
    return render_template('catalog.html', cassettes=cassettes, genres=genres, selected_genre=selected_genre)

@app.route('/cassette/<int:id>')
def product_details(id):
    cassette = Cassette.query.get_or_404(id)
    return render_template('product_details.html', cassette=cassette)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Валидация имени пользователя
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Валидация формата email
        if '@' not in email or '.' not in email:
            flash('Некорректный формат email')
            return redirect(url_for('register'))
        
        # Валидация email на уникальность
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Валидация длины пароля
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    cassettes = Cassette.query.all()
    return render_template('admin/dashboard.html', cassettes=cassettes)

@app.route('/admin/cassette/add', methods=['GET', 'POST'])
@login_required
def add_cassette():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    if request.method == 'POST':
        cassette = Cassette(
            title=request.form.get('title'),
            description=request.form.get('description'),
            release_year=request.form.get('release_year'),
            genre=request.form.get('genre'),
            price=float(request.form.get('price'))
        )
        db.session.add(cassette)
        db.session.flush()  # Get the cassette ID before commit
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_path = save_image(file, cassette.id)
                if image_path:
                    cassette.image_path = image_path
        
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('admin/add_cassette.html')

@app.route('/admin/cassette/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_cassette(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    cassette = Cassette.query.get_or_404(id)
    if request.method == 'POST':
        cassette.title = request.form.get('title')
        cassette.description = request.form.get('description')
        cassette.release_year = request.form.get('release_year')
        cassette.genre = request.form.get('genre')
        cassette.price = float(request.form.get('price'))
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_path = save_image(file, cassette.id)
                if image_path:
                    cassette.image_path = image_path
        
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('admin/edit_cassette.html', cassette=cassette)

@app.route('/admin/cassette/delete/<int:id>')
@login_required
def delete_cassette(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    cassette = Cassette.query.get_or_404(id)
    
    # Delete the image file if it exists
    if cassette.image_path and cassette.image_path != 'cassettes/default.jpg':
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], cassette.image_path.split('/')[-1]))
        except:
            pass
    
    db.session.delete(cassette)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/cassettes/export')
@login_required
def export_cassettes():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    # Получаем все кассеты из базы данных
    cassettes = Cassette.query.all()
    
    # Создаем буфер для записи CSV
    output = StringIO()
    csv_writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Записываем заголовки
    headers = ['ID', 'Название', 'Описание', 'Год выпуска', 'Жанр', 'Цена', 'Доступность']
    csv_writer.writerow(headers)
    
    # Записываем данные кассет
    for cassette in cassettes:
        # Форматируем цену как строку с запятой вместо точки
        price_str = str(cassette.price).replace('.', ',')
        
        row = [
            cassette.id,
            cassette.title,
            cassette.description,
            cassette.release_year,
            cassette.genre,
            price_str,  # Используем отформатированную строку
            'Да' if cassette.available else 'Нет'
        ]
        csv_writer.writerow(row)
    
    # Подготавливаем ответ с CSV файлом
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cassettes_{timestamp}.csv"
    
    # Отправляем файл пользователю
    return app.response_class(
        output.getvalue().encode('utf-8-sig'),  # utf-8-sig для корректного отображения кириллицы в Excel
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

# Rental routes
@app.route('/rent/<int:id>', methods=['POST'])
@login_required
def rent_cassette(id):
    cassette = Cassette.query.get_or_404(id)
    
    if not cassette.available:
        flash('Эта кассета сейчас недоступна')
        return redirect(url_for('product_details', id=id))
    
    # Check if user already has this cassette rented
    existing_rental = Rental.query.filter_by(
        user_id=current_user.id,
        cassette_id=id,
        is_returned=False
    ).first()
    
    if existing_rental:
        flash('Вы уже арендовали эту кассету')
        return redirect(url_for('product_details', id=id))
    
    # Create new rental
    rental = Rental(
        user_id=current_user.id,
        cassette_id=id,
        rental_date=datetime.utcnow()
    )
    cassette.available = False
    
    db.session.add(rental)
    db.session.commit()
    
    flash('Кассета успешно арендована')
    return redirect(url_for('rentals'))

@app.route('/return/<int:id>', methods=['POST'])
@login_required
def return_cassette(id):
    rental = Rental.query.filter_by(
        user_id=current_user.id,
        cassette_id=id,
        is_returned=False
    ).first_or_404()
    
    rental.is_returned = True
    rental.return_date = datetime.utcnow()
    rental.cassette.available = True
    
    db.session.commit()
    flash('Кассета успешно возвращена')
    return redirect(url_for('rentals'))

@app.route('/rentals')
@login_required
def rentals():
    active_rentals = Rental.query.filter_by(
        user_id=current_user.id,
        is_returned=False
    ).all()
    
    past_rentals = Rental.query.filter_by(
        user_id=current_user.id,
        is_returned=True
    ).order_by(Rental.return_date.desc()).all()
    
    return render_template('rentals.html', active_rentals=active_rentals, past_rentals=past_rentals)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 