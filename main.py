import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
API_TOKEN = '8541533138:AAFUws7UK5ZNdia57ZgfSZdcNyrrj67nS3Q'
bot = telebot.TeleBot(API_TOKEN)

user_contexts = {}


# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить историю диалога\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.chat.id
    if user_id in user_contexts:
        user_contexts[user_id] = []
        bot.reply_to(message, "История диалога очищена.")
    else:
        bot.reply_to(message, "История диалога уже пуста.")


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    try:
        response = requests.get('http://localhost:1234/v1/models')

        if response.status_code == 200:
            model_info = response.json()
            model_name = model_info['data'][0]['id']
            bot.reply_to(message, f"Используемая модель: {model_name}")
        else:
            bot.reply_to(message, 'Не удалось получить информацию о модели.')
    except Exception as e:
        bot.reply_to(message, f'Ошибка соединения с LM Studio: {e}')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_query = message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = []

    user_contexts[user_id].append({
        "role": "user",
        "content": user_query
    })

    request = {
        "messages": user_contexts[user_id],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }

    try:
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json=request
        )

        if response.status_code == 200:
            model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
            assistant_answer = model_response.choices[0].message.content

            user_contexts[user_id].append({
                "role": "assistant",
                "content": assistant_answer
            })

            bot.reply_to(message, assistant_answer)
        else:
            bot.reply_to(message, 'Произошла ошибка при обращении к модели.')
            user_contexts[user_id].pop()
    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка при обращении к модели: {e}')
        # Удаляем неудачный запрос из истории
        if user_id in user_contexts and user_contexts[user_id]:
            user_contexts[user_id].pop()


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
