#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для создания базы данных и загрузки начальных данных из Excel
Запуск: python init_db.py
"""

import os
import pandas as pd
from app import app, db
from app import Partner, ProductCategory, Product, Order, OrderItem

with app.app_context():
    print("=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # Создаём папку instance, если её нет
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("✅ Папка instance создана")
    
    # Создаём таблицы
    print("\n1. Создание таблиц...")
    db.create_all()
    print("   ✅ Таблицы созданы")
    
    # Проверяем, есть ли уже данные
    if ProductCategory.query.count() > 0:
        print("\n⚠️ Таблицы уже содержат данные!")
        response = input("Удалить все данные и загрузить заново? (y/n): ")
        if response.lower() != 'y':
            print("❌ Операция отменена")
            exit()
        
        # Очищаем таблицы
        print("\n2. Очистка существующих данных...")
        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        Partner.query.delete()
        ProductCategory.query.delete()
        db.session.commit()
        print("   ✅ Данные очищены")
    
    # Загружаем категории
    print("\n3. Загрузка категорий...")
    try:
        df = pd.read_excel('data/categories.xlsx')
        for _, row in df.iterrows():
            cat = ProductCategory(
                id=int(row['id']),
                name=row['name'],
                description=row.get('description', '')
            )
            db.session.add(cat)
        db.session.commit()
        print(f"   ✅ Добавлено {len(df)} категорий")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Загружаем партнёров
    print("\n4. Загрузка партнёров...")
    try:
        df = pd.read_excel('data/partners.xlsx')
        for _, row in df.iterrows():
            partner = Partner(
                id=int(row['id']),
                name=row['name'],
                short_name=row.get('short_name', ''),
                partner_type=row.get('partner_type', ''),
                director=row.get('director', ''),
                phone=row.get('phone', ''),
                discount=float(row.get('discount', 0)),
                total_orders_sum=0,  # Начальная сумма заказов
                actual_address=row.get('actual_address', ''),
                legal_address=row.get('legal_address', '')
            )
            db.session.add(partner)
        db.session.commit()
        print(f"   ✅ Добавлено {len(df)} партнёров")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Загружаем товары
    print("\n5. Загрузка товаров...")
    try:
        df = pd.read_excel('data/products.xlsx')
        # Преобразуем числовые поля
        df['alcohol_content'] = pd.to_numeric(df['alcohol_content'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        for _, row in df.iterrows():
            product = Product(
                id=int(row['id']),
                article=row['article'],
                name=row['name'],
                commercial_name=row.get('commercial_name', ''),
                unit=row.get('unit', 'шт'),
                base_price=float(row['base_price']),
                excise_tax=float(row.get('excise_tax', 0)),
                license_fee=float(row.get('license_fee', 0)),
                is_alcohol=bool(int(row.get('is_alcohol', 0))),
                alcohol_content=float(row['alcohol_content']) if pd.notna(row['alcohol_content']) else None,
                volume=float(row['volume']) if pd.notna(row['volume']) else None,
                category_id=int(row['category_id'])
            )
            db.session.add(product)
        db.session.commit()
        print(f"   ✅ Добавлено {len(df)} товаров")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Показываем статистику
    print("\n" + "=" * 50)
    print("СТАТИСТИКА")
    print("=" * 50)
    print(f"Категорий: {ProductCategory.query.count()}")
    print(f"Партнёров: {Partner.query.count()}")
    print(f"Товаров: {Product.query.count()}")
    print(f"Заявок: {Order.query.count()}")
    
    print("\n✅ База данных успешно инициализирована!")