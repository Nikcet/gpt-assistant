from config import TOKEN, OPENAI_TOKEN
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import openai

context_message: [str] = []

def start_command(update, context) -> None:
    user = update.message.from_user
    print(user)

    update.message.reply_text(text=f'Привет, {user.first_name}!\nВведи свой вопрос боту:')


def clear_context(update, context) -> None:
    global context_message
    context_message.clear()
    update.message.reply_text(text='Контекст очищен 😏')


def send_answer(update, context) -> None:
    global context_message
    question = update.message.text
    print(question)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Щас подумаю...')
    context_message.append(question)
    answer = request_to_ai(question)
    context_message.append(answer)
    print(answer)
    context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


def request_to_ai(text: str) -> str:
    context_string = ' '.join(context_message)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": context_string},
            {"role": "user", "content": text}
        ]
    )
    return completion.choices[0].message['content']


def main() -> None:
    # Авторизация в OpenAI
    openai.api_key = OPENAI_TOKEN

    # Инициализируем бота с помощью токена
    updater = Updater(token=TOKEN, use_context=True)

    # Создаем слушатель всех событий. Нужнен для перенаправления входящих на сервер telegram'а событий разным обработчикам
    dispatcher = updater.dispatcher

    # Создаем обработчики команд /start и /mem
    start_handler = CommandHandler('start', start_command)
    clear_handler = CommandHandler('clear_context', clear_context)
    # Создаем обработчик входящих сообщений с фильтром - обрабатываем только получение текстовых сообщений
    echo_handler = MessageHandler(Filters.text, send_answer)

    # Соединяем обработчики событий со слушателем этих событий
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(clear_handler)
    dispatcher.add_handler(echo_handler)

    # Запускаем бота
    print('Бот успешно запущен!')
    updater.start_polling()


# Вызываем функцию main
if __name__ == '__main__':
    main()
