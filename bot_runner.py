import requests
import time
from telegram_bot import bot_handlers

def poll_telegram_updates():
    """Опрос обновлений от Telegram"""
    offset = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot8134047471:AAFhVz8wZKocQBmTTfd3eyq3zKG8q1hoIE8/getUpdates"
            params = {'offset': offset, 'timeout': 30}
            
            response = requests.get(url, params=params, timeout=35)
            updates = response.json()
            
            if updates.get('ok'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', '')
                        
                        print(f"📨 Получено сообщение: {text} от {chat_id}")
                        
                        # Обработка команд
                        if text == '/start':
                            bot_handlers['handle_start'](chat_id, message)
                        elif text == '/help' or text == 'ℹ️ Помощь':
                            bot_handlers['handle_help'](chat_id)
                        elif text == '🏆 Турниры':
                            bot_handlers['handle_tournaments'](chat_id)
                        elif text == '📊 Рейтинг':
                            bot_handlers['handle_rating'](chat_id)
                        elif text == '👤 Мой профиль':
                            bot_handlers['handle_profile'](chat_id, message)
                        elif text == '📅 Активные турниры':
                            bot_handlers['handle_active_tournaments'](chat_id)
                        elif text == '✅ Мои регистрации':
                            bot_handlers['handle_my_registrations'](chat_id, message)
                        elif text == '🔙 Назад':
                            bot_handlers['handle_back'](chat_id)
                        else:
                            bot_handlers['send_message'](chat_id, 
                                "❌ Неизвестная команда. Используйте кнопки меню или /help для справки.",
                                bot_handlers['handle_back'].__self__.get_main_menu_keyboard())
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Ошибка в боте: {e}")
            time.sleep(5)

if __name__ == '__main__':
    print("🤖 Запуск Telegram бота...")
    print("🔗 Бот готов к работе!")
    print("📱 Перейдите в бота: https://t.me/floppoker_bot")
    poll_telegram_updates()
