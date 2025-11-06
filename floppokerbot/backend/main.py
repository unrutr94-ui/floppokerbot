from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["http://localhost:8000", "http://127.0.0.1:8000"])

def init_db():
    conn = sqlite3.connect('poker_tournament.db')
    cursor = conn.cursor()
    
    # Удаляем старые таблицы если они существуют
    cursor.execute("DROP TABLE IF EXISTS registrations")
    cursor.execute("DROP TABLE IF EXISTS tournaments") 
    cursor.execute("DROP TABLE IF EXISTS rating")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            salt TEXT,
            telegram_username TEXT UNIQUE,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            role TEXT DEFAULT 'player',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица турниров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_by INTEGER,
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Таблица регистраций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            user_id INTEGER,
            tournament_id INTEGER,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, tournament_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
        )
    ''')
    
    # Таблица рейтинга
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rating (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            telegram_username TEXT UNIQUE,
            score INTEGER DEFAULT 1000,
            created_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Создаём администраторов
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ESV65'")
    if cursor.fetchone()[0] == 0:
        # Администратор ESV65
        password_hash, salt = hash_password("admin123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?, ?, ?, ?, ?)",
            ('ESV65', password_hash, salt, 'Тестовый Директор', 'director')
        )
        
        # Администратор Tummik01
        password_hash2, salt2 = hash_password("flopadmin0123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?, ?, ?, ?, ?)",
            ('Tummik01', password_hash2, salt2, 'Администратор Tummik', 'director')
        )
        
        director_id = cursor.lastrowid
        
        # Тестовые игроки
        test_players = [
            ('ivanov', 123456789, 'Иван Иванов'),
            ('petrov', 987654321, 'Петр Петров'),
            ('sidorov', 555555555, 'Сидор Сидоров'),
        ]
        
        for telegram_username, telegram_id, full_name in test_players:
            cursor.execute(
                "INSERT INTO users (telegram_username, telegram_id, full_name, role) VALUES (?, ?, ?, 'player')",
                (telegram_username, telegram_id, full_name)
            )
            
            # Создаем запись в рейтинге для каждого игрока
            cursor.execute(
                "INSERT INTO rating (player_name, telegram_username, score, created_by) VALUES (?, ?, ?, ?)",
                (full_name, telegram_username, 1000, director_id)
            )
        
        # Тестовые турниры
        test_tournaments = [
            ("Воскресный турнир", 600, 30000, 600, 30000, 900, 30000, 15, "2024-01-15 20:00:00", "2024-01-15 19:45:00", director_id),
            ("Быстрый покер", 300, 15000, 300, 15000, 450, 15000, 10, "2024-01-16 19:00:00", "2024-01-16 18:45:00", director_id),
        ]
        cursor.executemany(
            "INSERT INTO tournaments (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            test_tournaments
        )
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")
    print("👑 Администраторы созданы")
    print("🎮 Тестовые игроки созданы")

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

def get_db_connection():
    conn = sqlite3.connect('poker_tournament.db')
    conn.row_factory = sqlite3.Row
    return conn

def check_director_access(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return user and user['role'] == 'director'

# Аутентификация
@app.route('/api/auth/login', methods=['POST'])
def web_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Введите логин и пароль'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, password_hash, salt, full_name, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        if verify_password(password, user['password_hash'], user['salt']):
            return jsonify({
                'success': True, 
                'message': 'Успешный вход',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'auth_type': 'web'
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Неверный пароль'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/auth/telegram', methods=['POST'])
def telegram_login():
    data = request.json
    telegram_username = data.get('telegram_username')
    
    if not telegram_username:
        return jsonify({'success': False, 'message': 'Введите Telegram username'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, telegram_username, telegram_id, full_name, role FROM users WHERE telegram_username = ?", (telegram_username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Игрок не найден'})
        
        return jsonify({
            'success': True, 
            'message': 'Успешный вход',
            'user': {
                'id': user['id'],
                'telegram_username': user['telegram_username'],
                'telegram_id': user['telegram_id'],
                'full_name': user['full_name'],
                'role': user['role'],
                'auth_type': 'telegram'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Управление игроками
@app.route('/api/admin/create_player', methods=['POST'])
def create_player():
    data = request.json
    director_id = data.get('user_id')
    
    if not check_director_access(director_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    telegram_username = data.get('telegram_username')
    full_name = data.get('full_name')
    
    if not telegram_username or not full_name:
        return jsonify({'success': False, 'message': 'Все поля обязательны'})
    
    if telegram_username.startswith('@'):
        telegram_username = telegram_username[1:]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE telegram_username = ?", (telegram_username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Игрок уже существует'})
        
        # Создаем игрока
        cursor.execute(
            "INSERT INTO users (telegram_username, full_name, role) VALUES (?, ?, 'player')",
            (telegram_username, full_name)
        )
        
        player_id = cursor.lastrowid
        
        # Автоматически создаем запись в рейтинге
        cursor.execute(
            "INSERT INTO rating (player_name, telegram_username, score, created_by) VALUES (?, ?, ?, ?)",
            (full_name, telegram_username, 1000, director_id)
        )
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Игрок {full_name} создан'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/admin/players', methods=['GET'])
def get_players():
    user_id = request.args.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT u.id, u.telegram_username, u.full_name, u.role, u.created_at, 
                   COALESCE(r.score, 1000) as rating_score
            FROM users u 
            LEFT JOIN rating r ON u.telegram_username = r.telegram_username
            WHERE u.role = 'player' 
            ORDER BY u.created_at DESC
        ''')
        
        players = cursor.fetchall()
        result = []
        for player in players:
            result.append({
                'id': player['id'],
                'telegram_username': player['telegram_username'],
                'full_name': player['full_name'],
                'role': player['role'],
                'created_at': player['created_at'],
                'rating_score': player['rating_score']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/admin/players/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    data = request.json
    director_id = data.get('user_id')
    
    if not check_director_access(director_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем telegram_username игрока перед удалением
        cursor.execute("SELECT telegram_username FROM users WHERE id = ?", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            return jsonify({'success': False, 'message': 'Игрок не найден'})
        
        telegram_username = player['telegram_username']
        
        # Удаляем из рейтинга
        cursor.execute("DELETE FROM rating WHERE telegram_username = ?", (telegram_username,))
        
        # Удаляем регистрации
        cursor.execute("DELETE FROM registrations WHERE user_id = ?", (player_id,))
        
        # Удаляем игрока
        cursor.execute("DELETE FROM users WHERE id = ?", (player_id,))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Игрок удалён'})
            
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Управление турнирами
@app.route('/api/tournaments', methods=['GET', 'POST'])
def manage_tournaments():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT t.*, COUNT(r.user_id) as registered_players 
                FROM tournaments t 
                LEFT JOIN registrations r ON t.id = r.tournament_id 
                WHERE t.status = 'upcoming' 
                GROUP BY t.id 
                ORDER BY t.start_time
            ''')
            tournaments = cursor.fetchall()
            
            result = []
            for t in tournaments:
                result.append({
                    'id': t['id'],
                    'name': t['name'],
                    'rent_cost': t['rent_cost'],
                    'rent_chips': t['rent_chips'],
                    'rebuy_cost': t['rebuy_cost'],
                    'rebuy_chips': t['rebuy_chips'],
                    'addon_cost': t['addon_cost'],
                    'addon_chips': t['addon_chips'],
                    'level_time': t['level_time'],
                    'start_time': t['start_time'],
                    'late_reg_end_time': t['late_reg_end_time'],
                    'registered_players': t['registered_players'],
                    'status': t['status']
                })
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()
    
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        
        if not check_director_access(user_id):
            return jsonify({'success': False, 'message': 'Доступ запрещён'})
        
        name = data.get('name')
        rent_cost = data.get('rent_cost')
        rent_chips = data.get('rent_chips')
        rebuy_cost = data.get('rebuy_cost', 0)
        rebuy_chips = data.get('rebuy_chips', 0)
        addon_cost = data.get('addon_cost', 0)
        addon_chips = data.get('addon_chips', 0)
        level_time = data.get('level_time', 15)
        start_time = data.get('start_time')
        late_reg_end_time = data.get('late_reg_end_time')
        
        # Проверяем только основные обязательные поля
        if not name or rent_cost is None or rent_chips is None or not start_time or not late_reg_end_time:
            return jsonify({'success': False, 'message': 'Основные поля обязательны: название, аренда, время начала и окончания регистрации'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO tournaments (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, user_id)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Турнир создан'})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()

@app.route('/api/tournaments/<int:tournament_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_tournament(tournament_id):
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
            tournament = cursor.fetchone()
            
            if not tournament:
                return jsonify({'success': False, 'message': 'Турнир не найден'})
            
            cursor.execute('''
                SELECT u.telegram_username, u.full_name 
                FROM registrations r 
                JOIN users u ON r.user_id = u.id 
                WHERE r.tournament_id = ?
            ''', (tournament_id,))
            players_data = cursor.fetchall()
            
            registered_players = []
            for player in players_data:
                registered_players.append({
                    'telegram_username': player['telegram_username'],
                    'full_name': player['full_name']
                })
            
            actual_registered_players = len(registered_players)
            total_chips = (tournament['rent_chips'] * actual_registered_players) + (tournament['addon_chips'] * actual_registered_players)
            
            result = {
                'id': tournament['id'],
                'name': tournament['name'],
                'rent_cost': tournament['rent_cost'],
                'rent_chips': tournament['rent_chips'],
                'rebuy_cost': tournament['rebuy_cost'],
                'rebuy_chips': tournament['rebuy_chips'],
                'addon_cost': tournament['addon_cost'],
                'addon_chips': tournament['addon_chips'],
                'level_time': tournament['level_time'],
                'start_time': tournament['start_time'],
                'late_reg_end_time': tournament['late_reg_end_time'],
                'registered_players': actual_registered_players,
                'status': tournament['status'],
                'total_chips': total_chips,
                'players': registered_players
            }
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Ошибка загрузки турнира: {str(e)}'})
        finally:
            conn.close()
    
    # Для PUT и DELETE методов
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Отсутствуют данные'})
    
    user_id = data.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if request.method == 'PUT':
            name = data.get('name')
            rent_cost = data.get('rent_cost')
            rent_chips = data.get('rent_chips')
            rebuy_cost = data.get('rebuy_cost', 0)
            rebuy_chips = data.get('rebuy_chips', 0)
            addon_cost = data.get('addon_cost', 0)
            addon_chips = data.get('addon_chips', 0)
            level_time = data.get('level_time', 15)
            start_time = data.get('start_time')
            late_reg_end_time = data.get('late_reg_end_time')
            
            cursor.execute(
                "UPDATE tournaments SET name = ?, rent_cost = ?, rent_chips = ?, rebuy_cost = ?, rebuy_chips = ?, addon_cost = ?, addon_chips = ?, level_time = ?, start_time = ?, late_reg_end_time = ? WHERE id = ?",
                (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, tournament_id)
            )
            message = 'Турнир обновлён'
            
        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM registrations WHERE tournament_id = ?", (tournament_id,))
            cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
            message = 'Турнир удалён'
        
        conn.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Управление рейтингом
@app.route('/api/rating', methods=['GET', 'POST'])
def manage_rating():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM rating ORDER BY score DESC")
            rating_data = cursor.fetchall()
            
            result = []
            for r in rating_data:
                result.append({
                    'id': r['id'],
                    'player_name': r['player_name'],
                    'telegram_username': r['telegram_username'],
                    'score': r['score']
                })
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()
    
    elif request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Отсутствуют данные'})
        
        user_id = data.get('user_id')
        
        if not check_director_access(user_id):
            return jsonify({'success': False, 'message': 'Доступ запрещён'})
        
        player_name = data.get('player_name')
        telegram_username = data.get('telegram_username')
        score = data.get('score', 1000)
        
        if not player_name or not telegram_username:
            return jsonify({'success': False, 'message': 'Имя игрока и Telegram username обязательны'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO rating (player_name, telegram_username, score, created_by) VALUES (?, ?, ?, ?)",
                (player_name, telegram_username, score, user_id)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Игрок добавлен в рейтинг'})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)})
        finally:
            conn.close()

@app.route('/api/rating/<int:rating_id>', methods=['PUT', 'DELETE'])
def manage_rating_item(rating_id):
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Отсутствуют данные'})
    
    user_id = data.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if request.method == 'PUT':
            player_name = data.get('player_name')
            telegram_username = data.get('telegram_username')
            score = data.get('score')
            
            cursor.execute(
                "UPDATE rating SET player_name = ?, telegram_username = ?, score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (player_name, telegram_username, score, rating_id)
            )
            message = 'Рейтинг обновлён'
            
        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM rating WHERE id = ?", (rating_id,))
            message = 'Игрок удалён из рейтинга'
        
        conn.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Получение рейтинга игрока по telegram_username
@app.route('/api/rating/player/<telegram_username>', methods=['GET'])
def get_player_rating(telegram_username):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM rating WHERE telegram_username = ?", (telegram_username,))
        rating = cursor.fetchone()
        
        if not rating:
            return jsonify({'success': False, 'message': 'Рейтинг не найден'})
        
        # Получаем позицию в рейтинге
        cursor.execute("SELECT COUNT(*) FROM rating WHERE score > ?", (rating['score'],))
        position = cursor.fetchone()[0] + 1
        
        result = {
            'success': True,
            'rating': {
                'id': rating['id'],
                'player_name': rating['player_name'],
                'telegram_username': rating['telegram_username'],
                'score': rating['score'],
                'position': position
            }
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Получение полной информации о пользователе с рейтингом
@app.route('/api/user/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, telegram_username, full_name, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        result = {
            'id': user['id'],
            'telegram_username': user['telegram_username'],
            'full_name': user['full_name'],
            'role': user['role']
        }
        
        # Если это игрок, получаем его рейтинг и позицию
        if user['role'] == 'player' and user['telegram_username']:
            cursor.execute("SELECT * FROM rating WHERE telegram_username = ?", (user['telegram_username'],))
            rating = cursor.fetchone()
            
            if rating:
                # Получаем позицию в рейтинге
                cursor.execute("SELECT COUNT(*) FROM rating WHERE score > ?", (rating['score'],))
                position = cursor.fetchone()[0] + 1
                
                result['rating'] = {
                    'score': rating['score'],
                    'position': position
                }
            else:
                result['rating'] = {
                    'score': 1000,
                    'position': None
                }
        
        return jsonify({'success': True, 'profile': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Регистрация на турнир
@app.route('/api/register', methods=['POST'])
def register_for_tournament():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Отсутствуют данные'})
    
    user_id = data.get('user_id')
    tournament_id = data.get('tournament_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Необходима авторизация'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        cursor.execute("SELECT late_reg_end_time FROM tournaments WHERE id = ?", (tournament_id,))
        tournament = cursor.fetchone()
        
        if not tournament:
            return jsonify({'success': False, 'message': 'Турнир не найден'})
        
        late_reg_end_time = tournament['late_reg_end_time']
        
        # Проверяем время регистрации
        if datetime.now() > datetime.fromisoformat(late_reg_end_time.replace('Z', '+00:00')):
            return jsonify({'success': False, 'message': 'Поздняя регистрация завершена'})
        
        cursor.execute("SELECT 1 FROM registrations WHERE user_id = ? AND tournament_id = ?", (user_id, tournament_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Вы уже зарегистрированы на этот турнир'})
        
        cursor.execute(
            "INSERT INTO registrations (user_id, tournament_id) VALUES (?, ?)",
            (user_id, tournament_id)
        )
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Регистрация успешна'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# Health check
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'OK', 'message': 'Сервер работает'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
