import os
import psycopg2
import hashlib
import secrets
from datetime import datetime

def get_db_connection():
    """Подключение к PostgreSQL на вашем VPS"""
    database_url = "postgresql://poker_user:flopbot2024@85.92.111.75:5432/poker_club"
    conn = psycopg2.connect(database_url)
    return conn

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()
    return password_hash, salt

def verify_password(password, password_hash, salt):
    test_hash, _ = hash_password(password, salt)
    return test_hash == password_hash

def init_database():
    """Инициализация базы данных PostgreSQL на VPS"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                salt TEXT,
                telegram_username TEXT UNIQUE,
                telegram_id BIGINT UNIQUE,
                full_name TEXT,
                role TEXT DEFAULT 'player',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица турниров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                rent_cost INTEGER NOT NULL,
                rent_chips INTEGER NOT NULL,
                rebuy_cost INTEGER DEFAULT 0,
                rebuy_chips INTEGER DEFAULT 0,
                addon_cost INTEGER DEFAULT 0,
                addon_chips INTEGER DEFAULT 0,
                level_time INTEGER DEFAULT 15,
                start_time TIMESTAMP NOT NULL,
                late_reg_end_time TIMESTAMP NOT NULL,
                created_by INTEGER REFERENCES users(id),
                status TEXT DEFAULT 'registration',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица регистраций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                user_id INTEGER REFERENCES users(id),
                tournament_id INTEGER REFERENCES tournaments(id),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, tournament_id)
            )
        ''')
        
        # Таблица фишек игроков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_chips (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id),
                user_id INTEGER REFERENCES users(id),
                chips INTEGER DEFAULT 0,
                rebuys INTEGER DEFAULT 0,
                addons INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tournament_id, user_id)
            )
        ''')
        
        # Таблица рейтинга
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rating (
                id SERIAL PRIMARY KEY,
                player_name TEXT NOT NULL,
                telegram_username TEXT UNIQUE,
                score INTEGER DEFAULT 1000,
                created_by INTEGER REFERENCES users(id),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица столов турнира
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_tables (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id),
                table_number INTEGER,
                max_players INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица рассадки игроков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_assignments (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id),
                table_id INTEGER REFERENCES tournament_tables(id),
                user_id INTEGER REFERENCES users(id),
                seat_number INTEGER,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tournament_id, user_id)
            )
        ''')
        
        # Создаём администраторов если их нет
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ESV65'")
        result = cursor.fetchone()
        if result[0] == 0:
            # Администратор ESV65
            password_hash, salt = hash_password("admin123")
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (%s, %s, %s, %s, %s)",
                ('ESV65', password_hash, salt, 'Тестовый Директор', 'director')
            )
            
            # Администратор Tummik01
            password_hash2, salt2 = hash_password("flopadmin0123")
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (%s, %s, %s, %s, %s)",
                ('Tummik01', password_hash2, salt2, 'Администратор Tummik', 'director')
            )
            
            # Тестовые игроки
            test_players = [
                ('ivanov', 123456789, 'Иван Иванов'),
                ('petrov', 987654321, 'Петр Петров'),
                ('sidorov', 555555555, 'Сидор Сидоров'),
                ('smirnov', 111111111, 'Алексей Смирнов'),
                ('kuznetsov', 222222222, 'Дмитрий Кузнецов'),
                ('popov', 333333333, 'Андрей Попов'),
                ('volkov', 444444444, 'Сергей Волков'),
            ]
            
            for telegram_username, telegram_id, full_name in test_players:
                cursor.execute(
                    "INSERT INTO users (telegram_username, telegram_id, full_name, role) VALUES (%s, %s, %s, 'player')",
                    (telegram_username, telegram_id, full_name)
                )
                
                # Создаем запись в рейтинге для каждого игрока
                cursor.execute(
                    "INSERT INTO rating (player_name, telegram_username, score, created_by) VALUES (%s, %s, %s, 1)",
                    (full_name, telegram_username, 1000)
                )
        
        conn.commit()
        print("✅ VPS PostgreSQL база данных инициализирована")
        print("👑 Администраторы созданы")
        print("🎮 Тестовые игроки созданы")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка инициализации базы: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
