import sqlite3
import json

class API:
    def __init__(self):
        self.db = sqlite3.connect('contexts.db')
        self.db.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, context TEXT NOT NULL);")
        self.db.commit()
        self.db.close()

    def update_context(self, user_id: str, context: str) -> None:
        self.db = sqlite3.connect('contexts.db')
        cursor = self.db.cursor()
        cursor.execute("SELECT id, context FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        if result:
            # Пользователь существует, обновляем значение поля context
            current_context = json.loads(result[1])
            current_context.append(context)
            try:
                cursor.execute("UPDATE users SET context=? WHERE id=?", (json.dumps(current_context, ensure_ascii=False), user_id))
            except Exception as e:
                print('Не обновил контекст в базе данных:', e)
        else:
            try:
                # Пользователь не существует, создаем новую запись
                cursor.execute("INSERT INTO users (id, context) VALUES (?, ?)", (user_id, json.dumps([context], ensure_ascii=False)))
            except Exception as e:
                print('Пользователь не существует. Попытался создать нового пользователя в базе данных, но не вышло:', e)

        self.db.commit()
        self.db.close()

    def get_context(self, user_id: str) -> str:
        self.db = sqlite3.connect('contexts.db')
        cursor = self.db.execute("SELECT context FROM users WHERE id=?", (user_id,))
        try:
            row = cursor.fetchone()
            if not row:
                print(f'Пользователь {user_id} не найден')
                return ''
            context = json.loads(row[0])
            # print(context)
            return '; '.join(context)
        except Exception as e:
            print(f'Ошибка получения контекста пользователя {user_id}:', e)
            return ''
        finally:
            self.db.commit()
            self.db.close()

    def clear_context(self, user_id: str) -> None:
        with sqlite3.connect('contexts.db') as self.db:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            if cursor.rowcount > 0:
                print(f'Пользователь с id {user_id} удален')
                cursor.execute("INSERT INTO users (id, context) VALUES (?, ?)",
                               (user_id, json.dumps([], ensure_ascii=False)))
                print(f'Создана новая строка для пользователя с id {user_id}')
            else:
                print('Пользователь не найден.')

    def delete_some_context(self, user_id: str):
        self.db = sqlite3.connect('contexts.db')
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        if result:
            # Пользователь существует, обновляем значение поля context
            current_context: list = cursor.execute("SELECT context FROM users WHERE id=?", (user_id,)).fetchone()[0]
            new_context: list = current_context[5:]
            cursor.execute("UPDATE users SET context=? WHERE id=?", (json.dumps(new_context, ensure_ascii=False), user_id))
        else:
            # Пользователь не существует, создаем новую запись
            cursor.execute("INSERT INTO users (id, context) VALUES (?, ?)", (user_id, json.dumps([], ensure_ascii=False)))

        self.db.commit()
        self.db.close()

