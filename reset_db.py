#!/usr/bin/env python
# -*- coding: utf-8 -*-
from app import app, db
from app import Partner, ProductCategory, Product, Order, OrderItem

with app.app_context():
    print("=== ПОЛНЫЙ СБРОС БАЗЫ ДАННЫХ ===\n")
    
    print("1. Удаление таблиц...")
    db.drop_all()
    print("   ✅ Таблицы удалены")
    
    print("\n2. Создание таблиц...")
    db.create_all()
    print("   ✅ Таблицы созданы")
    
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Список таблиц: {', '.join(tables)}")
    
    print("\n3. Загрузка начальных данных...")
    import pandas as pd
    
    # Категории
    try:
        df_cat = pd.read_excel('data/categories.xlsx')
        for _, row in df_cat.iterrows():
            cat = ProductCategory(
                id=int(row['id']),
                name=row['name'],
                description=row.get('description', '')
            )
            db.session.add(cat)
        db.session.commit()
        print(f"   ✅ Добавлено {len(df_cat)} категорий")
    except Exception as e:
        print(f"   ❌ Ошибка загрузки категорий: {e}")
    
    # Партнёры
    try:
        df_part = pd.read_excel('data/partners.xlsx')
        for _, row in df_part.iterrows():
            partner = Partner(
                id=int(row['id']),
                name=row['name'],
                short_name=row.get('short_name', ''),
                partner_type=row.get('partner_type', ''),
                director=row.get('director', ''),
                phone=row.get('phone', ''),
                discount=float(row.get('discount', 0)),
                actual_address=row.get('actual_address', ''),
                legal_address=row.get('legal_address', '')
            )
            db.session.add(partner)
        db.session.commit()
        print(f"   ✅ Добавлено {len(df_part)} партнёров")
    except Exception as e:
        print(f"   ❌ Ошибка загрузки партнёров: {e}")
    
    # Товары
    try:
        df_prod = pd.read_excel('data/products.xlsx')
        df_prod['alcohol_content'] = pd.to_numeric(df_prod['alcohol_content'], errors='coerce')
        df_prod['volume'] = pd.to_numeric(df_prod['volume'], errors='coerce')
        
        for _, row in df_prod.iterrows():
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
        print(f"   ✅ Добавлено {len(df_prod)} товаров")
    except Exception as e:
        print(f"   ❌ Ошибка загрузки товаров: {e}")
    
    print("\n=== ПРОВЕРКА ===")
    print(f"Категорий: {ProductCategory.query.count()}")
    print(f"Партнёров: {Partner.query.count()}")
    print(f"Товаров: {Product.query.count()}")
    print(f"Заявок: {Order.query.count()}")
    
    print("\n✅ База данных готова!")