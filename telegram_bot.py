import os
import logging
import requests
import sqlite3
from datetime import datetime

# Настройки бота
BOT_TOKEN = "8134047471:AAFhVz8wZKocQBmTTfd3eyq3zKG8q1hoIE8"
BOT_USERNAME = "floppoker_bot"
BACKEND_URL = "https://floppokerbot.onrender.com"
FRONTEND_URL = "https://unrutr94-ui.github.io/floppokerbot"

def setup_telegram_bot():
    """Настройка Telegram бота"""
    
    def set_webhook():
        """Установка вебхука для бота"""
        webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        # Пока используем polling, позже настроим вебхук
        print("🤖 Telegram бот инициализирован")
        print(f"🔗 Ссылка на бота: https://t.me/{BOT_USERNAME}")
        
    def send_telegram_message(chat_id, text, reply_markup=None):
        """Отправка сообщения в Telegram"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
            
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            return False

    def get_main_menu_keyboard():
        """Клавиатура главного меню"""
        return {
            'keyboard': [
                [{'text': '🏆 Турниры'}, {'text': '📊 Рейтинг'}],
                [{'text': '👤 Мой профиль'}, {'text': 'ℹ️ Помощь'}]
            ],
            'resize_keyboard': True
        }

    def get_tournaments_keyboard():
        """Клавиатура для турниров"""
        return {
            'keyboard': [
                [{'text': '📅 Активные турниры'}, {'text': '✅ Мои регистрации'}],
                [{'text': '🔙 Назад'}]
            ],
            'resize_keyboard': True
        }

    def handle_start_command(chat_id, message):
        """Обработка команды /start"""
        user = message.get('from', {})
        first_name = user.get('first_name', '')
        username = user.get('username', '')
        
        welcome_text = f"""
👋 Привет, {first_name}!

Добро пожаловать в <b>Покерный Клуб</b>! 🎯

Здесь ты можешь:
🏆 Смотреть актуальные турниры
📊 Следить за рейтингом игроков  
✅ Регистрироваться на турниры
👤 Отслеживать свой прогресс

Используй кнопки ниже для навигации:
        """
        
        send_telegram_message(chat_id, welcome_text, get_main_menu_keyboard())
        save_telegram_user(chat_id, username, first_name, user.get('last_name', ''))

    def handle_help_command(chat_id):
        """Обработка команды помощи"""
        help_text = f"""
<b>📖 Справка по боту</b>

<b>Основные команды:</b>
🏆 Турниры - просмотр активных турниров
📊 Рейтинг - таблица лидеров  
👤 Мой профиль - информация о вас

<b>Регистрация на турниры:</b>
1. Нажмите "🏆 Турниры"
2. Выберите "📅 Активные турниры"
3. Используйте веб-версию для регистрации

<b>Веб-версия:</b>
Для полного доступа ко всем функциям используйте веб-версию:
<a href="{FRONTEND_URL}">{FRONTEND_URL}</a>
        """
        
        send_telegram_message(chat_id, help_text, get_main_menu_keyboard())

    def handle_tournaments_command(chat_id):
        """Показ меню турниров"""
        tournaments_text = f"""
<b>🏆 Управление турнирами</b>

Здесь вы можете:
• Просмотреть активные турниры
• Посмотреть свои регистрации  
• Зарегистрироваться на турниры

<b>Полный функционал:</b>
<a href="{FRONTEND_URL}">Открыть веб-версию</a>

Выберите опцию ниже:
        """
        
        send_telegram_message(chat_id, tournaments_text, get_tournaments_keyboard())

    def handle_active_tournaments(chat_id):
        """Показ активных турниров"""
        try:
            response = requests.get(f'{BACKEND_URL}/api/tournaments')
            tournaments = response.json()
            
            if not tournaments:
                send_telegram_message(chat_id, 
                    "📭 На данный момент нет активных турниров.", 
                    get_tournaments_keyboard())
                return
            
            text = "<b>📅 Активные турниры:</b>\n\n"
            
            for tournament in tournaments[:5]:  # Показываем первые 5
                start_time = datetime.fromisoformat(tournament['start_time'].replace('Z', '+00:00'))
                text += f"<b>{tournament['name']}</b>\n"
                text += f"💰 Стоимость: {tournament['rent_cost']} руб\n"
                text += f"🪙 Фишки: {tournament['rent_chips']:,}\n"
                text += f"⏰ Начало: {start_time.strftime('%d.%m %H:%M')}\n"
                text += f"👥 Игроков: {tournament['registered_players']}\n"
                text += f"📱 <a href='{FRONTEND_URL}'>Зарегистрироваться в веб-версии</a>\n\n"
            
            if len(tournaments) > 5:
                text += f"<i>И еще {len(tournaments) - 5} турниров...</i>\n\n"
            
            text += f"<b>Полный список:</b>\n<a href='{FRONTEND_URL}'>📱 Открыть веб-версию</a>"
            
            send_telegram_message(chat_id, text, get_tournaments_keyboard())
            
        except Exception as e:
            print(f"❌ Ошибка получения турниров: {e}")
            send_telegram_message(chat_id, 
                "❌ Ошибка загрузки турниров", 
                get_tournaments_keyboard())

    def handle_rating_command(chat_id):
        """Показ рейтинга"""
        try:
            response = requests.get(f'{BACKEND_URL}/api/rating')
            rating_data = response.json()
            
            if not rating_data:
                send_telegram_message(chat_id, 
                    "📊 Рейтинг игроков пуст", 
                    get_main_menu_keyboard())
                return
            
            text = "<b>🏆 Топ-10 игроков:</b>\n\n"
            
            for i, player in enumerate(rating_data[:10]):
                medal = ""
                if i == 0: medal = "🥇 "
                elif i == 1: medal = "🥈 "  
                elif i == 2: medal = "🥉 "
                
                text += f"{medal}<b>{i+1}. {player['player_name']}</b>\n"
                text += f"   Рейтинг: {player['score']}\n"
                text += f"   @{player['telegram_username']}\n\n"
            
            send_telegram_message(chat_id, text, get_main_menu_keyboard())
            
        except Exception as e:
            print(f"❌ Ошибка получения рейтинга: {e}")
            send_telegram_message(chat_id, 
                "❌ Ошибка загрузки рейтинга", 
                get_main_menu_keyboard())

    def handle_profile_command(chat_id, message):
        """Показ профиля пользователя"""
        try:
            username = message.get('from', {}).get('username', '')
            
            if not username:
                send_telegram_message(chat_id, 
                    "❌ Для просмотра профиля у вас должен быть установлен Telegram username")
                return
            
            # Получаем информацию о пользователе
            response = requests.get(f'{BACKEND_URL}/api/user/profile/telegram/{username}')
            
            if response.status_code != 200:
                send_telegram_message(chat_id,
                    "❌ Профиль не найден. Возможно, вы еще не зарегистрированы в системе.")
                return
            
            profile_data = response.json()
            
            text = f"<b>👤 Ваш профиль:</b>\n\n"
            text += f"<b>Имя:</b> {profile_data.get('full_name', 'Не указано')}\n"
            text += f"<b>Username:</b> @{username}\n"
            
            rating = profile_data.get('rating', {})
            if rating:
                text += f"<b>🏅 Рейтинг:</b> {rating.get('score', 'Нет')}\n"
                if rating.get('position'):
                    text += f"<b>📊 Позиция:</b> {rating['position']}\n"
            else:
                text += "<b>🏅 Рейтинг:</b> не определён\n"
            
            text += f"\n<a href='{FRONTEND_URL}'>📱 Открыть веб-версию для полного доступа</a>"
            
            send_telegram_message(chat_id, text, get_main_menu_keyboard())
            
        except Exception as e:
            print(f"❌ Ошибка получения профиля: {e}")
            send_telegram_message(chat_id, 
                "❌ Ошибка загрузки профиля", 
                get_main_menu_keyboard())

    def handle_my_registrations(chat_id, message):
        """Показ регистраций пользователя"""
        try:
            username = message.get('from', {}).get('username', '')
            
            if not username:
                send_telegram_message(chat_id,
                    "❌ Для просмотра регистраций у вас должен быть установлен Telegram username")
                return
            
            # Получаем активные турниры
            response = requests.get(f'{BACKEND_URL}/api/tournaments?status=active')
            tournaments = response.json()
            
            my_tournaments = []
            for tournament in tournaments:
                tourn_response = requests.get(f'{BACKEND_URL}/api/tournaments/{tournament["id"]}')
                if tourn_response.status_code == 200:
                    tourn_data = tourn_response.json()
                    # Проверяем регистрацию по username
                    for player in tourn_data.get('players', []):
                        if player.get('telegram_username') == username:
                            my_tournaments.append(tourn_data)
                            break
            
            if not my_tournaments:
                send_telegram_message(chat_id,
                    "📭 У вас нет активных регистраций на турниры",
                    get_tournaments_keyboard())
                return
            
            text = "<b>✅ Ваши регистрации:</b>\n\n"
            
            for tournament in my_tournaments[:3]:  # Показываем первые 3
                status_badge = ""
                if tournament['status'] == 'registration': status_badge = "📝"
                elif tournament['status'] == 'active': status_badge = "🎮"  
                elif tournament['status'] == 'completed': status_badge = "🏁"
                
                text += f"{status_badge} <b>{tournament['name']}</b>\n"
                text += f"Статус: {tournament['status']}\n"
                text += f"<a href='{FRONTEND_URL}'>📱 Подробнее в веб-версии</a>\n\n"
            
            if len(my_tournaments) > 3:
                text += f"<i>И еще {len(my_tournaments) - 3} регистраций...</i>\n\n"
            
            text += f"<b>Все регистрации:</b>\n<a href='{FRONTEND_URL}'>📱 Открыть веб-версию</a>"
            
            send_telegram_message(chat_id, text, get_tournaments_keyboard())
            
        except Exception as e:
            print(f"❌ Ошибка получения регистраций: {e}")
            send_telegram_message(chat_id, 
                "❌ Ошибка загрузки регистраций", 
                get_tournaments_keyboard())

    def handle_back_command(chat_id):
        """Возврат в главное меню"""
        send_telegram_message(chat_id, 
            "🔙 Возврат в главное меню", 
            get_main_menu_keyboard())

    def save_telegram_user(chat_id, username, first_name, last_name):
        """Сохранение пользователя Telegram"""
        try:
            if not username:
                return
                
            full_name = f"{first_name} {last_name}".strip()
            
            # Отправляем запрос к бэкенду для создания/обновления пользователя
            user_data = {
                'telegram_username': username,
                'telegram_id': chat_id,
                'full_name': full_name
            }
            
            # Можно добавить endpoint в бэкенд для синхронизации пользователей
            print(f"👤 Пользователь Telegram: @{username} ({full_name})")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения пользователя: {e}")

    # Устанавливаем вебхук
    set_webhook()
    
    return {
        'send_message': send_telegram_message,
        'handle_start': handle_start_command,
        'handle_help': handle_help_command,
        'handle_tournaments': handle_tournaments_command,
        'handle_active_tournaments': handle_active_tournaments,
        'handle_rating': handle_rating_command,
        'handle_profile': handle_profile_command,
        'handle_my_registrations': handle_my_registrations,
        'handle_back': handle_back_command
    }

# Инициализация бота
bot_handlers = setup_telegram_bot()
