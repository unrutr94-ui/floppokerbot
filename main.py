from flask import Flask, jsonify, request
from flask_cors import CORS
import hashlib
import secrets
from datetime import datetime
import random
import os
from database import get_db_connection, init_database, hash_password, verify_password

app = Flask(__name__)
CORS(app, origins=[
    "https://unrutr94-ui.github.io",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
])

def check_director_access(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user and user[0] == 'director'

def get_tournament_status(tournament):
    """Определяет статус турнира на основе времени"""
    now = datetime.now()
    start_time = tournament['start_time']
    late_reg_end_time = tournament['late_reg_end_time']
    
    if tournament['status'] == 'completed':
        return 'completed'
    elif tournament['status'] == 'active_no_late_reg':
        return 'active_no_late_reg'
    elif tournament['status'] == 'active':
        if now < late_reg_end_time:
            return 'late_registration'
        else:
            return 'active'
    elif now < start_time:
        return 'registration'
    elif now < late_reg_end_time:
        return 'late_registration'
    else:
        return 'active'

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
        cursor.execute("SELECT id, username, password_hash, salt, full_name, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        if verify_password(password, user[2], user[3]):
            return jsonify({
                'success': True, 
                'message': 'Успешный вход',
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[4],
                    'role': user[5],
                    'auth_type': 'web'
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Неверный пароль'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
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
        cursor.execute("SELECT id, telegram_username, telegram_id, full_name, role FROM users WHERE telegram_username = %s", (telegram_username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Игрок не найден'})
        
        return jsonify({
            'success': True, 
            'message': 'Успешный вход',
            'user': {
                'id': user[0],
                'telegram_username': user[1],
                'telegram_id': user[2],
                'full_name': user[3],
                'role': user[4],
                'auth_type': 'telegram'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
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
        cursor.execute("SELECT id FROM users WHERE telegram_username = %s", (telegram_username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Игрок уже существует'})
        
        cursor.execute(
            "INSERT INTO users (telegram_username, full_name, role) VALUES (%s, %s, 'player')",
            (telegram_username, full_name)
        )
        
        cursor.execute(
            "INSERT INTO rating (player_name, telegram_username, score, created_by) VALUES (%s, %s, %s, %s)",
            (full_name, telegram_username, 1000, director_id)
        )
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Игрок {full_name} создан'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
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
                'id': player[0],
                'telegram_username': player[1],
                'full_name': player[2],
                'role': player[3],
                'created_at': player[4],
                'rating_score': player[5]
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
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
        cursor.execute("SELECT telegram_username FROM users WHERE id = %s", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            return jsonify({'success': False, 'message': 'Игрок не найден'})
        
        telegram_username = player[0]
        
        cursor.execute("DELETE FROM rating WHERE telegram_username = %s", (telegram_username,))
        cursor.execute("DELETE FROM registrations WHERE user_id = %s", (player_id,))
        cursor.execute("DELETE FROM table_assignments WHERE user_id = %s", (player_id,))
        cursor.execute("DELETE FROM player_chips WHERE user_id = %s", (player_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (player_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Игрок удалён'})
            
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Управление турнирами
@app.route('/api/tournaments', methods=['GET', 'POST'])
def manage_tournaments():
    if request.method == 'GET':
        status_filter = request.args.get('status', 'active')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if status_filter == 'completed':
                cursor.execute('''
                    SELECT t.*, COUNT(r.user_id) as registered_players 
                    FROM tournaments t 
                    LEFT JOIN registrations r ON t.id = r.tournament_id 
                    WHERE t.status = 'completed'
                    GROUP BY t.id 
                    ORDER BY t.start_time DESC
                ''')
            else:
                cursor.execute('''
                    SELECT t.*, COUNT(r.user_id) as registered_players 
                    FROM tournaments t 
                    LEFT JOIN registrations r ON t.id = r.tournament_id 
                    WHERE t.status != 'completed'
                    GROUP BY t.id 
                    ORDER BY t.start_time
                ''')
                
            tournaments = cursor.fetchall()
            
            result = []
            for t in tournaments:
                tournament_dict = {
                    'id': t[0], 'name': t[1], 'rent_cost': t[2], 'rent_chips': t[3],
                    'rebuy_cost': t[4], 'rebuy_chips': t[5], 'addon_cost': t[6],
                    'addon_chips': t[7], 'level_time': t[8], 'start_time': t[9],
                    'late_reg_end_time': t[10], 'registered_players': t[16]
                }
                
                status = get_tournament_status(tournament_dict)
                tournament_dict['status'] = status
                tournament_dict['db_status'] = t[12]
                
                result.append(tournament_dict)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            cursor.close()
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
        
        if not name or rent_cost is None or rent_chips is None or not start_time or not late_reg_end_time:
            return jsonify({'success': False, 'message': 'Основные поля обязательны'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO tournaments (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, created_by, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'registration')",
                (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, user_id)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Турнир создан'})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)})
        finally:
            cursor.close()
            conn.close()

@app.route('/api/tournaments/<int:tournament_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_tournament(tournament_id):
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
            tournament = cursor.fetchone()
            
            if not tournament:
                return jsonify({'success': False, 'message': 'Турнир не найден'})
            
            # Получаем зарегистрированных игроков с их фишками
            cursor.execute('''
                SELECT u.id, u.full_name, u.telegram_username, COALESCE(rat.score, 1000) as rating,
                       COALESCE(pc.chips, t.rent_chips) as chips,
                       COALESCE(pc.rebuys, 0) as rebuys,
                       COALESCE(pc.addons, 0) as addons
                FROM registrations r 
                JOIN users u ON r.user_id = u.id 
                LEFT JOIN rating rat ON u.telegram_username = rat.telegram_username
                LEFT JOIN player_chips pc ON r.tournament_id = pc.tournament_id AND r.user_id = pc.user_id
                CROSS JOIN tournaments t ON t.id = r.tournament_id
                WHERE r.tournament_id = %s
                ORDER BY 
                    CASE 
                        WHEN t.status IN ('active', 'late_registration', 'active_no_late_reg') THEN -pc.chips
                        ELSE u.full_name
                    END
            ''', (tournament_id,))
            players_data = cursor.fetchall()
            
            registered_players = []
            total_chips = 0
            for player in players_data:
                player_chips = player[4]
                total_chips += player_chips
                registered_players.append({
                    'user_id': player[0],
                    'game_nickname': player[1],
                    'rating': player[3],
                    'chips': player_chips,
                    'rebuys': player[5],
                    'addons': player[6]
                })
            
            actual_registered_players = len(registered_players)
            
            tournament_dict = {
                'id': tournament[0], 'name': tournament[1], 'rent_cost': tournament[2],
                'rent_chips': tournament[3], 'rebuy_cost': tournament[4], 'rebuy_chips': tournament[5],
                'addon_cost': tournament[6], 'addon_chips': tournament[7], 'level_time': tournament[8],
                'start_time': tournament[9], 'late_reg_end_time': tournament[10], 'status': tournament[12]
            }
            
            status = get_tournament_status(tournament_dict)
            
            result = {
                'id': tournament[0],
                'name': tournament[1],
                'rent_cost': tournament[2],
                'rent_chips': tournament[3],
                'rebuy_cost': tournament[4],
                'rebuy_chips': tournament[5],
                'addon_cost': tournament[6],
                'addon_chips': tournament[7],
                'level_time': tournament[8],
                'start_time': tournament[9],
                'late_reg_end_time': tournament[10],
                'registered_players': actual_registered_players,
                'status': status,
                'db_status': tournament[12],
                'total_chips': total_chips,
                'players': registered_players
            }
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Ошибка загрузки турнира: {str(e)}'})
        finally:
            cursor.close()
            conn.close()
    
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
                "UPDATE tournaments SET name = %s, rent_cost = %s, rent_chips = %s, rebuy_cost = %s, rebuy_chips = %s, addon_cost = %s, addon_chips = %s, level_time = %s, start_time = %s, late_reg_end_time = %s WHERE id = %s",
                (name, rent_cost, rent_chips, rebuy_cost, rebuy_chips, addon_cost, addon_chips, level_time, start_time, late_reg_end_time, tournament_id)
            )
            message = 'Турнир обновлён'
            
        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM table_assignments WHERE tournament_id = %s", (tournament_id,))
            cursor.execute("DELETE FROM tournament_tables WHERE tournament_id = %s", (tournament_id,))
            cursor.execute("DELETE FROM registrations WHERE tournament_id = %s", (tournament_id,))
            cursor.execute("DELETE FROM player_chips WHERE tournament_id = %s", (tournament_id,))
            cursor.execute("DELETE FROM tournaments WHERE id = %s", (tournament_id,))
            message = 'Турнир удалён'
        
        conn.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Запуск турнира
@app.route('/api/tournaments/<int:tournament_id>/start', methods=['POST'])
def start_tournament(tournament_id):
    data = request.json
    user_id = data.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE tournaments SET status = 'active' WHERE id = %s", (tournament_id,))
        
        # Инициализируем фишки для всех зарегистрированных игроков
        cursor.execute('''
            INSERT INTO player_chips (tournament_id, user_id, chips)
            SELECT r.tournament_id, r.user_id, t.rent_chips
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.tournament_id = %s
            ON CONFLICT (tournament_id, user_id) DO NOTHING
        ''', (tournament_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Турнир запущен. Поздняя регистрация доступна.'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Закрытие поздней регистрации
@app.route('/api/tournaments/<int:tournament_id>/close-late-reg', methods=['POST'])
def close_late_registration(tournament_id):
    data = request.json
    user_id = data.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE tournaments SET status = 'active_no_late_reg' WHERE id = %s", (tournament_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Поздняя регистрация закрыта'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Завершение турнира
@app.route('/api/tournaments/<int:tournament_id>/complete', methods=['POST'])
def complete_tournament(tournament_id):
    data = request.json
    user_id = data.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE tournaments SET status = 'completed' WHERE id = %s", (tournament_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Турнир завершён'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Обновление фишек игрока
@app.route('/api/tournaments/<int:tournament_id>/update-chips', methods=['POST'])
def update_player_chips(tournament_id):
    data = request.json
    user_id = data.get('user_id')
    player_user_id = data.get('player_user_id')
    chips = data.get('chips')
    rebuys = data.get('rebuys', 0)
    addons = data.get('addons', 0)
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    if chips is None:
        return jsonify({'success': False, 'message': 'Количество фишек обязательно'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO player_chips (tournament_id, user_id, chips, rebuys, addons, updated_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (tournament_id, user_id) 
            DO UPDATE SET chips = EXCLUDED.chips, rebuys = EXCLUDED.rebuys, addons = EXCLUDED.addons, updated_at = CURRENT_TIMESTAMP
        ''', (tournament_id, player_user_id, chips, rebuys, addons))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Фишки обновлены'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
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
                    'id': r[0],
                    'player_name': r[1],
                    'telegram_username': r[2],
                    'score': r[3]
                })
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
        finally:
            cursor.close()
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
                "INSERT INTO rating (player_name, telegram_username, score, created_by) VALUES (%s, %s, %s, %s)",
                (player_name, telegram_username, score, user_id)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Игрок добавлен в рейтинг'})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': str(e)})
        finally:
            cursor.close()
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
                "UPDATE rating SET player_name = %s, telegram_username = %s, score = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (player_name, telegram_username, score, rating_id)
            )
            message = 'Рейтинг обновлён'
            
        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM rating WHERE id = %s", (rating_id,))
            message = 'Игрок удалён из рейтинга'
        
        conn.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Получение рейтинга игрока по telegram_username
@app.route('/api/rating/player/<telegram_username>', methods=['GET'])
def get_player_rating(telegram_username):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM rating WHERE telegram_username = %s", (telegram_username,))
        rating = cursor.fetchone()
        
        if not rating:
            return jsonify({'success': False, 'message': 'Рейтинг не найден'})
        
        cursor.execute("SELECT COUNT(*) FROM rating WHERE score > %s", (rating[3],))
        position = cursor.fetchone()[0] + 1
        
        result = {
            'success': True,
            'rating': {
                'id': rating[0],
                'player_name': rating[1],
                'telegram_username': rating[2],
                'score': rating[3],
                'position': position
            }
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Получение полной информации о пользователе с рейтингом
@app.route('/api/user/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, telegram_username, full_name, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        result = {
            'id': user[0],
            'telegram_username': user[1],
            'full_name': user[2],
            'role': user[3]
        }
        
        if user[3] == 'player' and user[1]:
            cursor.execute("SELECT * FROM rating WHERE telegram_username = %s", (user[1],))
            rating = cursor.fetchone()
            
            if rating:
                cursor.execute("SELECT COUNT(*) FROM rating WHERE score > %s", (rating[3],))
                position = cursor.fetchone()[0] + 1
                
                result['rating'] = {
                    'score': rating[3],
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
        cursor.close()
        conn.close()

# Получение профиля пользователя по Telegram username
@app.route('/api/user/profile/telegram/<username>', methods=['GET'])
def get_user_profile_by_telegram(username):
    """Получение профиля пользователя по Telegram username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT u.id, u.telegram_username, u.full_name, u.role,
                   r.score, 
                   (SELECT COUNT(*) + 1 FROM rating WHERE score > r.score) as position
            FROM users u 
            LEFT JOIN rating r ON u.telegram_username = r.telegram_username
            WHERE u.telegram_username = %s
        ''', (username,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            return jsonify({'success': False, 'message': 'Пользователь не найден'}), 404
        
        result = {
            'id': user_data[0],
            'telegram_username': user_data[1],
            'full_name': user_data[2],
            'role': user_data[3],
            'rating': {
                'score': user_data[4] or 1000,
                'position': user_data[5] if user_data[4] else None
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
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
        # Получаем информацию о пользователе (включая директоров)
        cursor.execute("SELECT id, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        cursor.execute("SELECT late_reg_end_time, status FROM tournaments WHERE id = %s", (tournament_id,))
        tournament = cursor.fetchone()
        
        if not tournament:
            return jsonify({'success': False, 'message': 'Турнир не найден'})
        
        late_reg_end_time = tournament[0]
        tournament_status = tournament[1]
        
        # Проверяем, можно ли ещё регистрироваться
        if tournament_status == 'completed':
            return jsonify({'success': False, 'message': 'Турнир завершён'})
        elif tournament_status == 'active_no_late_reg':
            return jsonify({'success': False, 'message': 'Поздняя регистрация закрыта'})
        elif tournament_status == 'active':
            # В активном турнире проверяем время поздней регистрации
            if datetime.now() > late_reg_end_time:
                return jsonify({'success': False, 'message': 'Поздняя регистрация завершена'})
        
        cursor.execute("SELECT 1 FROM registrations WHERE user_id = %s AND tournament_id = %s", (user_id, tournament_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Вы уже зарегистрированы на этот турнир'})
        
        cursor.execute(
            "INSERT INTO registrations (user_id, tournament_id) VALUES (%s, %s)",
            (user_id, tournament_id)
        )
        
        # Если турнир уже активен, добавляем фишки игроку
        if tournament_status == 'active':
            cursor.execute('''
                INSERT INTO player_chips (tournament_id, user_id, chips)
                SELECT t.id, %s, t.rent_chips
                FROM tournaments t
                WHERE t.id = %s
                ON CONFLICT (tournament_id, user_id) DO NOTHING
            ''', (user_id, tournament_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Регистрация успешна'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Создание столов для турнира
@app.route('/api/tournaments/<int:tournament_id>/create-tables', methods=['POST'])
def create_tournament_tables(tournament_id):
    data = request.json
    user_id = data.get('user_id')
    
    if not check_director_access(user_id):
        return jsonify({'success': False, 'message': 'Доступ запрещён'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем зарегистрированных игроков
        cursor.execute('''
            SELECT r.user_id 
            FROM registrations r 
            WHERE r.tournament_id = %s
        ''', (tournament_id,))
        players = cursor.fetchall()
        
        if not players:
            return jsonify({'success': False, 'message': 'Нет зарегистрированных игроков'})
        
        # Получаем уже распределенных игроков
        cursor.execute('''
            SELECT user_id, seat_number 
            FROM table_assignments 
            WHERE tournament_id = %s
        ''', (tournament_id,))
        existing_assignments = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Определяем игроков, которых нужно распределить
        players_to_assign = [p[0] for p in players if p[0] not in existing_assignments]
        
        if not players_to_assign:
            return jsonify({'success': False, 'message': 'Все игроки уже распределены'})
        
        # Удаляем старые столы если они есть
        cursor.execute("DELETE FROM tournament_tables WHERE tournament_id = %s", (tournament_id,))
        
        # Создаем новые столы
        players_count = len(players)
        tables_count = (players_count + 9) // 10  # Максимум 10 игроков за столом
        
        all_seats = []
        for table_num in range(1, tables_count + 1):
            cursor.execute(
                "INSERT INTO tournament_tables (tournament_id, table_number, max_players) VALUES (%s, %s, %s) RETURNING id",
                (tournament_id, table_num, 10)
            )
            table_id = cursor.fetchone()[0]
            
            # Случайные места от 1 до 10
            available_seats = list(range(1, 11))
            random.shuffle(available_seats)
            
            start_index = (table_num - 1) * 10
            end_index = min(start_index + 10, players_count)
            
            table_players = players[start_index:end_index]
            
            for i, player in enumerate(table_players):
                player_id = player[0]
                
                # Если игрок уже имеет место, сохраняем его
                if player_id in existing_assignments:
                    seat_number = existing_assignments[player_id]
                else:
                    # Иначе назначаем случайное свободное место
                    seat_number = available_seats[i % len(available_seats)]
                
                cursor.execute(
                    "INSERT INTO table_assignments (tournament_id, table_id, user_id, seat_number) VALUES (%s, %s, %s, %s) ON CONFLICT (tournament_id, user_id) DO UPDATE SET table_id = EXCLUDED.table_id, seat_number = EXCLUDED.seat_number",
                    (tournament_id, table_id, player_id, seat_number)
                )
                all_seats.append(seat_number)
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': f'Распределено {len(players_to_assign)} игроков по {tables_count} столам',
            'tables_count': tables_count,
            'players_count': players_count,
            'new_players_assigned': len(players_to_assign)
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Получение информации о столах турнира
@app.route('/api/tournaments/<int:tournament_id>/tables', methods=['GET'])
def get_tournament_tables(tournament_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT tt.id, tt.table_number, tt.max_players,
                   COUNT(ta.user_id) as current_players
            FROM tournament_tables tt
            LEFT JOIN table_assignments ta ON tt.id = ta.table_id
            WHERE tt.tournament_id = %s
            GROUP BY tt.id, tt.table_number, tt.max_players
            ORDER BY tt.table_number
        ''', (tournament_id,))
        tables = cursor.fetchall()
        
        result = []
        for table in tables:
            cursor.execute('''
                SELECT u.full_name, u.telegram_username, ta.seat_number,
                       COALESCE(r.score, 1000) as rating,
                       COALESCE(pc.chips, t.rent_chips) as chips
                FROM table_assignments ta
                JOIN users u ON ta.user_id = u.id
                LEFT JOIN rating r ON u.telegram_username = r.telegram_username
                LEFT JOIN player_chips pc ON ta.tournament_id = pc.tournament_id AND ta.user_id = pc.user_id
                CROSS JOIN tournaments t ON t.id = ta.tournament_id
                WHERE ta.table_id = %s
                ORDER BY ta.seat_number
            ''', (table[0],))
            players = cursor.fetchall()
            
            table_data = {
                'id': table[0],
                'table_number': table[1],
                'max_players': table[2],
                'current_players': table[3],
                'players': []
            }
            
            for player in players:
                table_data['players'].append({
                    'full_name': player[0],
                    'telegram_username': player[1],
                    'seat_number': player[2],
                    'rating': player[3],
                    'chips': player[4]
                })
            
            result.append(table_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# Health check
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'OK', 'message': 'Сервер работает'})

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    print("🗄️ Постоянная база данных PostgreSQL готова!")
    app.run(host='0.0.0.0', port=port, debug=False)
