# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mint-warehouse-secret-key-2025'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'warehouse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ========== МОДЕЛИ ==========

class Partner(db.Model):
    __tablename__ = 'partners'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    short_name = db.Column(db.String(100))
    partner_type = db.Column(db.String(50))
    director = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    discount = db.Column(db.Numeric(5, 2), default=0.00)
    total_orders_sum = db.Column(db.Numeric(12, 2), default=0.00)
    actual_address = db.Column(db.Text)
    legal_address = db.Column(db.Text)
    
    orders = db.relationship('Order', backref='partner', lazy=True)
    
    # ДОБАВЬТЕ ЭТОТ МЕТОД
    def calculate_discount(self):
        """Расчёт скидки на основе суммы заказов"""
        total = float(self.total_orders_sum) if self.total_orders_sum else 0
        if total >= 50000:
            return 20
        elif total >= 20000:
            return 10
        elif total >= 10000:
            return 5
        else:
            return 0
    
    def update_discount(self):
        """Обновить скидку партнёра"""
        self.discount = self.calculate_discount()
    
    def __repr__(self):
        return f'<Partner {self.name}>'
class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    commercial_name = db.Column(db.String(255))
    unit = db.Column(db.String(20), default='шт')
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    excise_tax = db.Column(db.Numeric(10, 2), default=0.00)
    license_fee = db.Column(db.Numeric(10, 2), default=0.00)
    is_alcohol = db.Column(db.Boolean, default=False)
    alcohol_content = db.Column(db.Numeric(5, 2), nullable=True)
    volume = db.Column(db.Numeric(10, 3), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.article}: {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.calculate_subtotal()
        return round(total, 2)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    def calculate_subtotal(self):
        base = float(self.price_per_unit) * float(self.quantity)
        discount = float(self.order.partner.discount) if self.order and self.order.partner else 0
        discounted_base = base * (1 - discount / 100)
        excise = float(self.product.excise_tax) * float(self.quantity)
        license = float(self.product.license_fee) * float(self.quantity)
        return round(discounted_base + excise + license, 2)
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'
    def calculate_subtotal(self):
        base = float(self.price_per_unit) * float(self.quantity)
        # Скидка берётся из партнёра (уже накопительная)
        discount = float(self.order.partner.discount) if self.order and self.order.partner else 0
        discounted_base = base * (1 - discount / 100)
        excise = float(self.product.excise_tax) * float(self.quantity)
        license = float(self.product.license_fee) * float(self.quantity)
        return round(discounted_base + excise + license, 2)
# ========== МАРШРУТЫ ==========

@app.route('/')
def index():
    orders = Order.query.order_by(Order.date_created.desc()).all()
    return render_template('index.html', orders=orders)

@app.route('/products')
def products():
    products = Product.query.all()
    categories = ProductCategory.query.all()
    return render_template('products.html', products=products, categories=categories)

@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        try:
            product = Product(
                article=request.form['article'],
                name=request.form['name'],
                commercial_name=request.form.get('commercial_name', ''),
                unit=request.form.get('unit', 'шт'),
                base_price=float(request.form['base_price']),
                excise_tax=float(request.form.get('excise_tax', 0)),
                license_fee=float(request.form.get('license_fee', 0)),
                is_alcohol='is_alcohol' in request.form,
                alcohol_content=float(request.form['alcohol_content']) if request.form.get('alcohol_content') else None,
                volume=float(request.form['volume']) if request.form.get('volume') else None,
                category_id=int(request.form['category_id'])
            )
            db.session.add(product)
            db.session.commit()
            flash(f'✅ Товар "{product.name}" добавлен!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    categories = ProductCategory.query.all()
    return render_template('product_form.html', product=None, categories=categories)

@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.article = request.form['article']
            product.name = request.form['name']
            product.commercial_name = request.form.get('commercial_name', '')
            product.unit = request.form.get('unit', 'шт')
            product.base_price = float(request.form['base_price'])
            product.excise_tax = float(request.form.get('excise_tax', 0))
            product.license_fee = float(request.form.get('license_fee', 0))
            product.is_alcohol = 'is_alcohol' in request.form
            product.alcohol_content = float(request.form['alcohol_content']) if request.form.get('alcohol_content') else None
            product.volume = float(request.form['volume']) if request.form.get('volume') else None
            product.category_id = int(request.form['category_id'])
            
            db.session.commit()
            flash(f'✅ Товар "{product.name}" обновлен!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    categories = ProductCategory.query.all()
    return render_template('product_form.html', product=product, categories=categories)

@app.route('/product/delete/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    if product.order_items:
        flash(f'❌ Нельзя удалить товар "{product.name}", он используется в заявках!', 'error')
        return redirect(url_for('products'))
    
    db.session.delete(product)
    db.session.commit()
    flash(f'✅ Товар "{product.name}" удален!', 'success')
    return redirect(url_for('products'))

@app.route('/partners')
def partners():
    partners = Partner.query.all()
    return render_template('partners.html', partners=partners)

@app.route('/partner/new', methods=['GET', 'POST'])
def new_partner():
    if request.method == 'POST':
        try:
            partner = Partner(
                name=request.form['name'],
                short_name=request.form.get('short_name', ''),
                partner_type=request.form.get('partner_type', ''),
                director=request.form.get('director', ''),
                phone=request.form.get('phone', ''),
                discount=float(request.form.get('discount', 0)),
                actual_address=request.form.get('actual_address', ''),
                legal_address=request.form.get('legal_address', '')
            )
            db.session.add(partner)
            db.session.commit()
            flash(f'✅ Партнер "{partner.name}" добавлен!', 'success')
            return redirect(url_for('partners'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('partner_form.html', partner=None)

@app.route('/partner/edit/<int:id>', methods=['GET', 'POST'])
def edit_partner(id):
    partner = Partner.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            partner.name = request.form['name']
            partner.short_name = request.form.get('short_name', '')
            partner.partner_type = request.form.get('partner_type', '')
            partner.director = request.form.get('director', '')
            partner.phone = request.form.get('phone', '')
            partner.discount = float(request.form.get('discount', 0))
            partner.actual_address = request.form.get('actual_address', '')
            partner.legal_address = request.form.get('legal_address', '')
            
            db.session.commit()
            flash(f'✅ Партнер "{partner.name}" обновлен!', 'success')
            return redirect(url_for('partners'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('partner_form.html', partner=partner)

@app.route('/partner/delete/<int:id>')
def delete_partner(id):
    partner = Partner.query.get_or_404(id)
    
    if partner.orders:
        flash(f'❌ Нельзя удалить партнера "{partner.name}", у него есть заявки!', 'error')
        return redirect(url_for('partners'))
    
    db.session.delete(partner)
    db.session.commit()
    flash(f'✅ Партнер "{partner.name}" удален!', 'success')
    return redirect(url_for('partners'))

@app.route('/partner/<int:id>')
def partner_detail(id):
    partner = Partner.query.get_or_404(id)
    orders = Order.query.filter_by(partner_id=id).order_by(Order.date_created.desc()).all()
    return render_template('partner_detail.html', partner=partner, orders=orders)

@app.route('/categories')
def categories():
    categories = ProductCategory.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/category/new', methods=['GET', 'POST'])
def new_category():
    if request.method == 'POST':
        try:
            category = ProductCategory(
                name=request.form['name'],
                description=request.form.get('description', '')
            )
            db.session.add(category)
            db.session.commit()
            flash('✅ Категория добавлена!', 'success')
            return redirect(url_for('categories'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('category_form.html', category=None)

@app.route('/category/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    category = ProductCategory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            category.name = request.form['name']
            category.description = request.form.get('description', '')
            db.session.commit()
            flash('✅ Категория обновлена!', 'success')
            return redirect(url_for('categories'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('category_form.html', category=category)

@app.route('/category/delete/<int:id>')
def delete_category(id):
    category = ProductCategory.query.get_or_404(id)
    
    if category.products:
        flash('❌ Нельзя удалить категорию, в которой есть товары!', 'error')
        return redirect(url_for('categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('✅ Категория удалена!', 'success')
    return redirect(url_for('categories'))

@app.route('/category/<int:id>')
def category_detail(id):
    category = ProductCategory.query.get_or_404(id)
    products = Product.query.filter_by(category_id=id).all()
    return render_template('category_detail.html', category=category, products=products)

@app.route('/order/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        try:
            # Генерация номера заявки
            last_order = Order.query.order_by(Order.id.desc()).first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            order_number = f"ZAK-{datetime.now().strftime('%Y%m')}-{new_num:04d}"
            
            # Создаём заявку
            order = Order(
                order_number=order_number,
                partner_id=int(request.form['partner_id'])
            )
            db.session.add(order)
            db.session.flush()
            
            # Добавляем позиции
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and float(quantities[i]) > 0:
                    item = OrderItem(
                        order_id=order.id,
                        product_id=int(product_ids[i]),
                        quantity=float(quantities[i]),
                        price_per_unit=float(prices[i])
                    )
                    db.session.add(item)
            
            # Сохраняем заявку
            db.session.commit()
            
            # ========== ОБНОВЛЯЕМ СУММУ ЗАКАЗОВ ПАРТНЁРА ==========
            partner = Partner.query.get(order.partner_id)
            if partner:
                # Получаем все заявки партнёра
                all_orders = Order.query.filter_by(partner_id=partner.id).all()
                total_sum = 0
                for o in all_orders:
                    total_sum += o.calculate_total()
                
                # Обновляем сумму и скидку
                partner.total_orders_sum = total_sum
                partner.discount = partner.calculate_discount()
                db.session.commit()
                
                print(f"📊 Партнёр {partner.name}: сумма заказов = {total_sum:.2f} ₽, скидка = {partner.discount}%")
            
            flash(f'✅ Заявка {order_number} создана!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            db.session.rollback()
    
    partners = Partner.query.all()
    products = Product.query.all()
    return render_template('order_form.html', partners=partners, products=products, order=None)
@app.route('/order/<int:id>')
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('order_detail.html', order=order)

@app.route('/order/delete/<int:id>')
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash('✅ Заявка удалена!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Запуск АлкоСклад...")
    app.run(debug=True, host='0.0.0.0')