from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import os
from werkzeug.utils import secure_filename
import csv
from io import StringIO, BytesIO
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jewelrystore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/jewelry'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # client, regular_client, master, admin
    avatar = db.Column(db.String(200), default='avatars/default.jpg')
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    client = db.relationship('Client', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date)
    is_regular = db.Column(db.Boolean, default=False)
    orders_count = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    orders = db.relationship('Order', backref='client', lazy=True)

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_price_per_gram = db.Column(db.Float, nullable=False, default=0.0)
    jewelry_items = db.relationship('Jewelry', backref='material', lazy=True)

class Jewelry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    stone_type = db.Column(db.String(100))
    stone_carat = db.Column(db.Float)
    image_path = db.Column(db.String(200), default='jewelry/default.jpg')
    available = db.Column(db.Boolean, default=True)
    is_custom = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='jewelry', lazy=True)

class JewelryMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jewelry_id = db.Column(db.Integer, db.ForeignKey('jewelry.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    material_weight = db.Column(db.Float, nullable=False)  # вес использованного материала

class OrderStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    orders = db.relationship('Order', backref='status', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jewelry_id = db.Column(db.Integer, db.ForeignKey('jewelry.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('order_status.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    discount = db.Column(db.Float, default=0)
    final_price = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.String(500))
    size = db.Column(db.String(50))
    additional_notes = db.Column(db.Text)
    master_notes = db.Column(db.Text)
    is_custom = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def save_image(file, jewelry_id):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{jewelry_id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return f"jewelry/{filename}"
    return None

# Routes
@app.route('/')
def index():
    jewelry_items = Jewelry.query.filter_by(is_custom=False).all()
    return render_template('index.html', jewelry_items=jewelry_items)

@app.route('/catalog')
def catalog():
    # Получаем параметры фильтрации
    category = request.args.get('category')
    material = request.args.get('material')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    stone_type = request.args.get('stone_type')
    sort = request.args.get('sort', 'price_asc')
    
    # Начинаем с базового запроса
    query = Jewelry.query.filter_by(available=True, is_custom=False)
    
    # Применяем фильтры
    if category:
        query = query.filter_by(category=category)
    if material:
        query = query.filter_by(material_id=material)
    if price_min is not None:
        query = query.filter(Jewelry.price >= price_min)
    if price_max is not None:
        query = query.filter(Jewelry.price <= price_max)
    if stone_type:
        query = query.filter(Jewelry.stone_type == stone_type)
    
    # Применяем сортировку
    sort_options = {
        'price_asc': Jewelry.price.asc(),
        'price_desc': Jewelry.price.desc(),
        'name_asc': Jewelry.name.asc(),
        'name_desc': Jewelry.name.desc(),
        'weight_asc': Jewelry.weight.asc(),
        'weight_desc': Jewelry.weight.desc(),
        'date_asc': Jewelry.id.asc(),  # Используем id как приближение к дате создания
        'date_desc': Jewelry.id.desc()
    }
    
    query = query.order_by(sort_options.get(sort, Jewelry.price.asc()))
    
    # Получаем отфильтрованные украшения
    jewelry_items = query.all()
    
    # Получаем уникальные значения для фильтров
    categories = db.session.query(Jewelry.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    materials = Material.query.all()
    
    stone_types = db.session.query(Jewelry.stone_type).distinct().filter(Jewelry.stone_type.isnot(None)).all()
    stone_types = [stone[0] for stone in stone_types]
    
    # Получаем минимальную и максимальную цены для слайдера
    price_range = db.session.query(
        db.func.min(Jewelry.price),
        db.func.max(Jewelry.price)
    ).filter_by(available=True, is_custom=False).first()
    
    return render_template('catalog.html', 
                         jewelry_items=jewelry_items,
                         categories=categories,
                         materials=materials,
                         stone_types=stone_types,
                         price_range=price_range,
                         current_filters={
                             'category': category,
                             'material': material,
                             'price_min': price_min,
                             'price_max': price_max,
                             'stone_type': stone_type,
                             'sort': sort
                         })

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/jewelry/<int:id>')
def jewelry_detail(id):
    item = Jewelry.query.get_or_404(id)
    return render_template('jewelry_detail.html', item=item)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            # Проверяем, существует ли уже пользователь с таким username
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Пользователь с таким именем уже существует', 'danger')
                return redirect(url_for('register'))
            
            # Проверяем, существует ли уже пользователь с таким email
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Пользователь с таким email уже существует', 'danger')
                return redirect(url_for('register'))
            
            # Создаем нового пользователя с ролью 'client'
            user = User(
                username=username,
                email=email,
                role='client'
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Получаем ID пользователя
            
            # Создаем профиль клиента
            client = Client(
                user_id=user.id,
                last_name=request.form['last_name'],
                first_name=request.form['first_name'],
                middle_name=request.form.get('middle_name', ''),
                phone_number=request.form['phone_number'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            )
            db.session.add(client)
            db.session.commit()
            
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/custom_order', methods=['GET', 'POST'])
@login_required
def custom_order():
    if request.method == 'POST':
        # Создаем новое изделие
        jewelry = Jewelry(
            name=request.form.get('name'),
            type=request.form.get('type'),
            weight=0.0,  # будет рассчитано мастером
            price=0.0,  # будет установлено мастером
            is_custom=True
        )
        db.session.add(jewelry)
        db.session.commit()
        
        # Создаем заказ
        order = Order(
            jewelry_id=jewelry.id,
            client_id=current_user.client.id,
            delivery_address=request.form.get('delivery_address'),
            size=request.form.get('size'),
            additional_notes=request.form.get('additional_notes'),
            is_custom=True
        )
        db.session.add(order)
        db.session.commit()
        
        # Добавляем материалы
        for material_id in request.form.getlist('materials'):
            material_weight = float(request.form.get(f'material_weight_{material_id}'))
            jewelry_material = JewelryMaterial(
                jewelry_id=jewelry.id,
                material_id=material_id,
                material_weight=material_weight
            )
            db.session.add(jewelry_material)
        
        db.session.commit()
        flash('Ваш индивидуальный заказ успешно создан!', 'success')
        return redirect(url_for('index'))
    
    materials = Material.query.all()
    return render_template('custom_order.html', materials=materials)

@app.route('/admin/orders/<int:id>/approve', methods=['POST'])
@login_required
def approve_order(id):
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет доступа к этой странице', 'danger')
    return redirect(url_for('index'))

    order = Order.query.get_or_404(id)
    order.status_id = request.form.get('status_id')
    order.final_price = float(request.form.get('price'))
    order.master_notes = request.form.get('master_notes')
    
    # Обновляем цену изделия, если это индивидуальный заказ
    if order.is_custom:
        order.jewelry.price = order.final_price
    
    db.session.commit()
    flash('Заказ успешно подтвержден!', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    orders = Order.query.all()
    jewelry_items = Jewelry.query.all()
    materials = Material.query.all()
    clients = Client.query.all()
    
    return render_template('admin/dashboard.html', 
                         orders=orders,
                         jewelry_items=jewelry_items,
                         materials=materials,
                         clients=clients)

@app.route('/admin/jewelry')
@login_required
def admin_jewelry():
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    jewelry = Jewelry.query.all()
    materials = Material.query.all()
    return render_template('admin/jewelry.html', 
                         jewelry=jewelry,
                         materials=materials)

@app.route('/admin/materials')
@login_required
def admin_materials():
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет прав для доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    materials = Material.query.all()
    return render_template('admin/materials.html', materials=materials)

@app.route('/admin/materials/add', methods=['POST'])
@login_required
def admin_materials_add():
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        current_price_per_gram = float(request.form.get('current_price_per_gram', 0))
        
        if not name or current_price_per_gram <= 0:
            flash('Пожалуйста, заполните все обязательные поля корректно', 'danger')
            return redirect(url_for('admin_materials'))
        
        material = Material(
            name=name,
            description=description,
            current_price_per_gram=current_price_per_gram
        )
        db.session.add(material)
        db.session.commit()
        flash('Материал успешно добавлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении материала: {str(e)}', 'danger')
    
    return redirect(url_for('admin_materials'))

@app.route('/admin/materials/edit/<int:id>', methods=['POST'])
@login_required
def admin_materials_edit(id):
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    try:
        material = Material.query.get_or_404(id)
        material.name = request.form.get('name')
        material.description = request.form.get('description')
        material.current_price_per_gram = float(request.form.get('current_price_per_gram', 0))
        
        if not material.name or material.current_price_per_gram <= 0:
            flash('Пожалуйста, заполните все обязательные поля корректно', 'danger')
            return redirect(url_for('admin_materials'))
        
        db.session.commit()
        flash('Материал успешно обновлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении материала: {str(e)}', 'danger')
    
    return redirect(url_for('admin_materials'))

@app.route('/admin/materials/delete/<int:id>', methods=['POST'])
@login_required
def admin_materials_delete(id):
    if current_user.role not in ['admin', 'master']:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    try:
        material = Material.query.get_or_404(id)
        db.session.delete(material)
        db.session.commit()
        flash('Материал успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении материала: {str(e)}', 'danger')
    
    return redirect(url_for('admin_materials'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if current_user.role not in ['admin', 'master']:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.order_date.desc()).all()
    statuses = OrderStatus.query.all()
    return render_template('admin/orders.html', orders=orders, statuses=statuses)

@app.route('/admin/orders/edit/<int:id>', methods=['POST'])
@login_required
def admin_orders_edit(id):
    if current_user.role not in ['admin', 'master']:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    try:
        order = Order.query.get_or_404(id)
        
        # Обновляем статус
        new_status_id = request.form.get('status_id')
        if new_status_id:
            order.status_id = new_status_id
        
        # Обновляем цену
        new_price = request.form.get('final_price')
        if new_price:
            order.final_price = float(new_price)
        
        # Обновляем примечания мастера
        master_notes = request.form.get('master_notes')
        if master_notes is not None:
            order.master_notes = master_notes
        
        db.session.commit()
        flash('Заказ успешно обновлен', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении заказа: {str(e)}', 'danger')
    
    return redirect(url_for('admin_orders'))

# Добавляем свойства для отображения статуса заказа
@property
def status_display(self):
    status_names = {
        'new': 'Новый',
        'processing': 'В обработке',
        'ready': 'Готов к выдаче',
        'completed': 'Выполнен',
        'cancelled': 'Отменён'
    }
    return status_names.get(self.status_id, self.status_id)

@property
def status_color(self):
    status_colors = {
        'new': 'primary',
        'processing': 'warning',
        'ready': 'info',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return status_colors.get(self.status_id, 'secondary')

Order.status_display = status_display
Order.status_color = status_color

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/orders')
@login_required
def orders():
    # Получаем клиента текущего пользователя
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        flash('Профиль клиента не найден', 'danger')
        return redirect(url_for('profile'))
    
    # Получаем заказы клиента с связанными данными
    user_orders = Order.query.filter_by(client_id=client.id)\
        .join(Jewelry)\
        .join(OrderStatus)\
        .order_by(Order.order_date.desc())\
        .all()
    
    return render_template('orders.html', orders=user_orders)

@app.route('/admin/clients')
@login_required
def admin_clients():
    if current_user.role != 'admin':
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    # Получаем всех клиентов с информацией о пользователе
    clients = db.session.query(Client, User).join(User, Client.user_id == User.id).all()
    return render_template('admin/clients.html', clients=clients)

@app.route('/admin/clients/add', methods=['POST'])
@login_required
def admin_clients_add():
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Создаем пользователя
        user = User(
            email=request.form['email'],
            role='client'
        )
        user.set_password('default_password')  # Временный пароль
        db.session.add(user)
        db.session.flush()  # Получаем ID пользователя
        
        # Создаем клиента
        client = Client(
            user_id=user.id,
            last_name=request.form['last_name'],
            first_name=request.form['first_name'],
            middle_name=request.form.get('middle_name', ''),
            phone_number=request.form['phone_number'],
            birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d'),
            is_regular=bool(request.form.get('is_regular'))
        )
        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно добавлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении клиента: {str(e)}', 'danger')
    
    return redirect(url_for('admin_clients'))

@app.route('/admin/clients/edit/<int:id>', methods=['POST'])
@login_required
def admin_clients_edit(id):
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    client = Client.query.get_or_404(id)
    try:
        # Обновляем данные пользователя
        client.user.email = request.form['email']
        
        # Обновляем данные клиента
        client.last_name = request.form['last_name']
        client.first_name = request.form['first_name']
        client.middle_name = request.form.get('middle_name', '')
        client.phone_number = request.form['phone_number']
        client.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d')
        client.is_regular = bool(request.form.get('is_regular'))
        
        db.session.commit()
        flash('Данные клиента успешно обновлены', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении данных клиента: {str(e)}', 'danger')
    
    return redirect(url_for('admin_clients'))

@app.route('/admin/clients/delete/<int:id>', methods=['POST'])
@login_required
def admin_clients_delete(id):
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    client = Client.query.get_or_404(id)
    try:
        user = client.user
        db.session.delete(client)
        db.session.delete(user)
        db.session.commit()
        flash('Клиент успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении клиента: {str(e)}', 'danger')
    
    return redirect(url_for('admin_clients'))

@app.route('/admin/jewelry/add', methods=['POST'])
@login_required
def admin_jewelry_add():
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    try:
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        material_id = request.form['material_id']
        price = float(request.form['price'])
        weight = float(request.form['weight'])
        
        # Handle file upload
        if 'image' not in request.files:
            flash('Не выбрано изображение', 'danger')
            return redirect(url_for('admin_jewelry'))
            
        file = request.files['image']
        if file.filename == '':
            flash('Не выбрано изображение', 'danger')
            return redirect(url_for('admin_jewelry'))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            jewelry = Jewelry(
                name=name,
                description=description,
                category=category,
                material_id=material_id,
                price=price,
                weight=weight,
                image_path=f'jewelry/{filename}'
            )
            
            db.session.add(jewelry)
            db.session.commit()
            flash('Украшение успешно добавлено', 'success')
        else:
            flash('Недопустимый формат файла', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении украшения: {str(e)}', 'danger')
    
    return redirect(url_for('admin_jewelry'))

@app.route('/admin/jewelry/edit/<int:id>', methods=['POST'])
@login_required
def admin_jewelry_edit(id):
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    jewelry = Jewelry.query.get_or_404(id)
    try:
        jewelry.name = request.form['name']
        jewelry.description = request.form['description']
        jewelry.category = request.form['category']
        jewelry.material_id = request.form['material_id']
        jewelry.price = float(request.form['price'])
        jewelry.weight = float(request.form['weight'])
        
        # Handle file upload if new image is provided
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                if file and allowed_file(file.filename):
                    # Delete old image
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(jewelry.image_path))
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    jewelry.image_path = f'jewelry/{filename}'
                else:
                    flash('Недопустимый формат файла', 'danger')
                    return redirect(url_for('admin_jewelry'))
        
        db.session.commit()
        flash('Украшение успешно обновлено', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении украшения: {str(e)}', 'danger')
    
    return redirect(url_for('admin_jewelry'))

@app.route('/admin/jewelry/delete/<int:id>', methods=['POST'])
@login_required
def admin_jewelry_delete(id):
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    jewelry = Jewelry.query.get_or_404(id)
    try:
        # Delete image file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(jewelry.image_path))
        if os.path.exists(image_path):
            os.remove(image_path)
        
        db.session.delete(jewelry)
        db.session.commit()
        flash('Украшение успешно удалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении украшения: {str(e)}', 'danger')
    
    return redirect(url_for('admin_jewelry'))

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            # Создаем директорию для аватаров, если она не существует
            avatars_dir = os.path.join(app.static_folder, 'avatars')
            if not os.path.exists(avatars_dir):
                os.makedirs(avatars_dir)
            
            # Обновляем данные пользователя
            current_user.username = request.form.get('username')
            current_user.email = request.form.get('email')
            
            # Обновляем данные клиента
            client = Client.query.filter_by(user_id=current_user.id).first()
            if client:
                client.last_name = request.form.get('last_name')
                client.first_name = request.form.get('first_name')
                client.middle_name = request.form.get('middle_name')
                client.phone_number = request.form.get('phone_number')
                if request.form.get('birth_date'):
                    client.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()
            
            # Обрабатываем загруженный аватар
            avatar = request.files.get('avatar')
            if avatar and allowed_file(avatar.filename):
                # Удаляем старый аватар, если он не дефолтный
                if current_user.avatar != 'avatars/default.jpg':
                    old_avatar_path = os.path.join(app.static_folder, current_user.avatar)
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)
                
                filename = secure_filename(f"{current_user.id}_{uuid.uuid4()}_{avatar.filename}")
                avatar_path = os.path.join(avatars_dir, filename)
                avatar.save(avatar_path)
                current_user.avatar = f'avatars/{filename}'
            
            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении профиля: {str(e)}', 'danger')
    
    client = Client.query.filter_by(user_id=current_user.id).first()
    return render_template('edit_profile.html', client=client)

def seed_database():
    # Создаем материалы
    materials = [
        Material(name='Золото 585', price_per_gram=3500),
        Material(name='Серебро 925', price_per_gram=100),
        Material(name='Платина 950', price_per_gram=4500)
    ]
    for material in materials:
        db.session.add(material)
    db.session.commit()
    
    # Создаем украшения
    jewelry_items = [
        {
            'name': 'Кольцо "Лунный свет"',
            'type': 'кольцо',
            'description': 'Элегантное кольцо из белого золота с бриллиантом',
            'price': 25000,
            'weight': 5.2,
            'image_path': 'jewelry/moon_ring.jpg',
            'materials': ['Золото 585']
        },
        {
            'name': 'Серьги "Звездная пыль"',
            'type': 'серьги',
            'description': 'Серьги из серебра с сапфирами',
            'price': 15000,
            'weight': 8.5,
            'image_path': 'jewelry/star_earrings.jpg',
            'materials': ['Серебро 925']
        },
        {
            'name': 'Подвеска "Солнечный луч"',
            'type': 'подвеска',
            'description': 'Подвеска из желтого золота с цитрином',
            'price': 18000,
            'weight': 6.8,
            'image_path': 'jewelry/sun_pendant.jpg',
            'materials': ['Золото 585']
        },
        {
            'name': 'Браслет "Морская волна"',
            'type': 'браслет',
            'description': 'Браслет из платины с аквамаринами',
            'price': 35000,
            'weight': 12.3,
            'image_path': 'jewelry/wave_bracelet.jpg',
            'materials': ['Платина 950']
        },
        {
            'name': 'Колье "Лесная сказка"',
            'type': 'колье',
            'description': 'Колье из серебра с изумрудами',
            'price': 28000,
            'weight': 15.7,
            'image_path': 'jewelry/forest_necklace.jpg',
            'materials': ['Серебро 925']
        },
        {
            'name': 'Обручальное кольцо',
            'type': 'кольцо',
            'description': 'Классическое обручальное кольцо из белого золота',
            'price': 32000,
            'weight': 4.8,
            'image_path': 'jewelry/engagement_ring.jpg',
            'materials': ['Золото 585']
        }
    ]

    for item in jewelry_items:
        jewelry = Jewelry(
            name=item['name'],
            type=item['type'],
            description=item['description'],
            price=item['price'],
            weight=item['weight'],
            image_path=item['image_path']
        )
        for material_name in item['materials']:
            material = Material.query.filter_by(name=material_name).first()
            if material:
                jewelry_material = JewelryMaterial(
                    jewelry_item=jewelry,
                    material=material,
                    material_weight=item['weight']
                )
                db.session.add(jewelry_material)
        db.session.add(jewelry)
    db.session.commit()
    
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('У вас нет прав для доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/edit/<int:id>', methods=['POST'])
@login_required
def admin_users_edit(id):
    if current_user.role != 'admin, master':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    try:
        user = User.query.get_or_404(id)
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        password = request.form.get('password')
        
        # Проверяем, не занят ли новый логин другим пользователем
        if username != user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Пользователь с таким логином уже существует', 'danger')
                return redirect(url_for('admin_users'))
        
        # Проверяем, не занят ли новый email другим пользователем
        if email != user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Пользователь с таким email уже существует', 'danger')
                return redirect(url_for('admin_users'))
        
        user.username = username
        user.email = email
        user.role = role
        
        if password:
            user.set_password(password)
    
        db.session.commit()
        flash('Данные пользователя успешно обновлены', 'success') 
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении данных пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def admin_users_delete(id):
    if current_user.role != 'admin':
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    try:
        # Нельзя удалить самого себя
        if user.id == current_user.id:
            flash('Вы не можете удалить свой собственный аккаунт', 'danger')
            return redirect(url_for('admin_users'))
        
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/create_order/<int:jewelry_id>', methods=['POST'])
@login_required
def create_order(jewelry_id):
    try:
        # Получаем украшение
        jewelry = Jewelry.query.get_or_404(jewelry_id)
        
        # Получаем клиента
        client = Client.query.filter_by(user_id=current_user.id).first()
        if not client:
            flash('Пожалуйста, заполните профиль клиента', 'danger')
            return redirect(url_for('profile'))
        
        # Проверяем, заполнены ли все обязательные поля
        if not all([client.last_name, client.first_name, client.phone_number]):
            flash('Пожалуйста, заполните все обязательные поля в профиле (Фамилия, Имя, Телефон)', 'danger')
            return redirect(url_for('edit_profile'))
        
        # Получаем статус "В ожидании"
        pending_status = OrderStatus.query.filter_by(name='В ожидании').first()
        if not pending_status:
            pending_status = OrderStatus(name='В ожидании')
            db.session.add(pending_status)
            db.session.flush()
        
        # Создаем заказ
        order = Order(
            jewelry_id=jewelry.id,
            client_id=client.id,
            status_id=pending_status.id,
            order_date=datetime.utcnow(),
            final_price=jewelry.price,
            delivery_address=request.form.get('delivery_address'),
            size=request.form.get('size'),
            additional_notes=request.form.get('additional_notes')
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash('Заказ успешно создан!', 'success')
        return redirect(url_for('orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при создании заказа: {str(e)}', 'danger')
        return redirect(url_for('catalog'))

@app.route('/order/<int:id>')
@login_required
def order_details(id):
    # Получаем клиента текущего пользователя
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        flash('Профиль клиента не найден', 'danger')
        return redirect(url_for('profile'))
    
    # Получаем заказ с связанными данными
    order = Order.query.filter_by(id=id, client_id=client.id)\
        .join(Jewelry)\
        .join(OrderStatus)\
        .first_or_404()
    
    return render_template('order_details.html', order=order)

@app.route('/order/<int:id>/pdf')
@login_required
def download_order_pdf(id):
    try:
        # Получаем клиента текущего пользователя
        client = Client.query.filter_by(user_id=current_user.id).first()
        if not client:
            flash('Профиль клиента не найден', 'danger')
            return redirect(url_for('profile'))
        
        # Получаем заказ с связанными данными
        order = Order.query.filter_by(id=id, client_id=client.id)\
            .join(Jewelry)\
            .join(OrderStatus)\
            .first_or_404()
        
        # Создаем PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Устанавливаем шрифт Helvetica
        p.setFont("Helvetica", 12)
        
        # Заголовок
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, f'Заказ #{order.id}')
        p.setFont("Helvetica", 12)
        
        # Информация о заказе
        y = 700
        p.drawString(50, y, f'Дата заказа: {order.order_date.strftime("%d.%m.%Y")}')
        y -= 20
        p.drawString(50, y, f'Статус: {order.status.name}')
        y -= 20
        p.drawString(50, y, f'Изделие: {order.jewelry.name}')
        y -= 20
        p.drawString(50, y, f'Сумма: {order.final_price} ₽')
        y -= 40
        
        # Информация о клиенте
        p.drawString(50, y, 'Информация о клиенте:')
        y -= 20
        p.drawString(50, y, f'ФИО: {client.full_name}')
        y -= 20
        p.drawString(50, y, f'Телефон: {client.phone_number}')
        y -= 20
        if current_user.email:
            p.drawString(50, y, f'Email: {current_user.email}')
        
        # Сохраняем PDF
        p.showPage()
        p.save()
        
        # Перемещаем указатель в начало буфера
        buffer.seek(0)
        
        # Отправляем PDF как файл для скачивания
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'order_{order.id}.pdf'
        )
        
    except Exception as e:
        flash(f'Ошибка при создании PDF: {str(e)}', 'danger')
        return redirect(url_for('orders'))

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 