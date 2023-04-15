from config import TOKEN, OPENAI_TOKEN, TEST_TOKEN
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai
import json
import datetime
from SQLite_API import API as DB


class App:
    ERROR_FILE = 'errors.json'
    CONTEXT_FILE = 'context.json'


    def __init__(self) -> None:
        # Авторизация в OpenAI
        openai.api_key = OPENAI_TOKEN

        # Инициализируем бота с помощью токена
        self.updater = Updater(token=TOKEN, use_context=True)

        # Инициализируем sql таблицу
        self.db = DB()

        # Создаем слушатель всех событий. Нужнен для перенаправления входящих на сервер telegram'а событий разным обработчикам
        self.dispatcher = self.updater.dispatcher

        # Создаем обработчики команд /start и /clear_context
        self.start_handler = CommandHandler('start', self.start_command)
        self.clear_handler = CommandHandler('clear_context', self.delete_context_and_send_message)
        # Создаем обработчик входящих сообщений с фильтром - обрабатываем только получение текстовых сообщений
        self.echo_handler = MessageHandler(Filters.text, self.send_answer)

        # Соединяем обработчики событий со слушателем этих событий
        self.dispatcher.add_handler(self.start_handler)
        self.dispatcher.add_handler(self.clear_handler)
        self.dispatcher.add_handler(self.echo_handler)

        # Запускаем бота
        self.updater.start_polling()
        print('Бот успешно запущен!')

    def start_command(self, update, context: CallbackContext) -> None:
        update.message.reply_text(
            text="""
Привет!

Этот бот открывает вам доступ к нейросетевой модели ChatGPT от компании OpenAI. 

⚡️Бот использует ту же модель, что и сайт ChatGPT: gpt-3.5-turbo.

Чатбот умеет:
1. Писать и редактировать тексты; 
2. Переводить с любого языка на любой; 
3. Писать и редактировать код; 
4. Отвечать на вопросы; 
5. Генерировать идеи; 
6. Многое другое. 

Вы можете общаться с ботом, как с живым собеседником, задавая вопросы на любом языке. Обратите внимание, что иногда бот придумывает факты, а также обладает ограниченными знаниями о событиях после 2021 года.

Бот отвечает на вопросы, учитывая контекст общения. Он запоминает все ваши вопросы и свои собственные ответы. Но длина запросов ограничена примерно 4000 символов кириллицы с учетом контекста. Поэтому, при смене темы вопроса, рекомендуется чистить контекст диалога с помощью команды /clear_context 
(контекст хранится до тех пор, пока вы его не очистите, другие данные не хранятся).

Так же учитывайте, что бот может трактовать одни и те же события по разному, поэтому не воспринимайте ответы бота как истину в последней инстанции. 

📋 Когда даете боту задание, пишите запрос максимально подробно. Если бот где-то допустил ошибку, напишите ему об этом - он исправит. 

Помните, что этот бот - нейросетевая машина - и писать запросы для него нужно, как для машины. И тогда он сослужит вам добрую службу.

⏳ Время ответа бота зависит от сложности вопроса и объема ответа. 
Он может ответить через секунду, а может через несколько минут. Но среднее время ответа бота - 7-15 секунд.
        """)

    def save_to_file(self, file: str, data: dict) -> None:
        try:
            with open(f"{file}", 'a', encoding='utf8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(e)

    def send_answer(self, update, context: CallbackContext) -> None:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Щас подумаю...')

        question = update.message.text
        user_id = str(update.message.from_user.id)

        self.db.update_context(user_id, question)
        context_message = self.db.get_context(user_id)

        # Делает запрос к серверу OpenAI
        answer = self.request_to_ai(question, context_message, user_id)
        self.db.update_context(user_id, answer)

        context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

    def request_to_ai(self, text: str, context: str, user_id) -> str:
        request_time = datetime.datetime.now()
        for i in range(1, 6):
            try:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": text}
                    ]
                )
            except Exception as e:
                error = f'Длина вопроса и контекста превышена. Чистит контекст. {e}\nВопрос: {text}. Попытка: {i}'
                self.save_to_file(self.ERROR_FILE, {
                    'Error': {
                        'message': error,
                        'time': request_time.strftime("%H:%M:%S %Y-%m-%d")
                    }
                })
                self.db.delete_some_context(user_id)
                continue

            return completion.choices[0].message['content']
        else:
            return 'Не удалось отправить запрос на сервер. Попробуйте очистить контекст и повторить попытку.'

    def delete_context_and_send_message(self, update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        try:
            self.db.clear_context(user_id)
        except Exception as e:
            self.db.update_context(user_id, ' ')
            print('Ошибка ключа. Такого ключа не существует. Создал нового пользователя.', e)
        finally:
            update.message.reply_text(text='Контекст очищен.')


if __name__ == '__main__':
    App()
