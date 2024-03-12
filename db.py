import sqlite3
from datetime import datetime

class PostDatabase:
    def __init__(self, db_name='posts.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self._create_table()
    
    def _create_table(self):
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            photo_url TEXT,
            active BOOLEAN NOT NULL CHECK (active IN (0,1)),
            post_time DATETIME NOT NULL
        )
        ''')
        self.conn.commit()

    def add_record(self, title, text, photo_url, post_time):
        self.c.execute('''
        INSERT INTO posts (title, text, photo_url, active, post_time)
        VALUES (?, ?, ?, 1, ?)
        ''', (title, text, photo_url, post_time))
        self.conn.commit()

    def read_all_records(self):
        self.c.execute('SELECT * FROM posts')
        rows = self.c.fetchall()
        columns = [column[0] for column in self.c.description]
        return [dict(zip(columns, row)) for row in rows]

    def update_active_status(self, id, active):
        self.c.execute('''
        UPDATE posts
        SET active = ?
        WHERE id = ?
        ''', (active, id))
        self.conn.commit()

    def get_last_id(self):
        self.c.execute('SELECT MAX(id) FROM posts')
        max_id = self.c.fetchone()[0]
        if max_id is None:
            return 1  # Возвращает 1, если нет записей, для совместимости с предыдущим кодом
        else:
            return max_id  # Возвращает максимальный id, а не следующий

    def close(self):
        self.conn.close()

# Пример использования класса
if __name__ == '__main__':
    db = PostDatabase()
    db.add_record('Title 1', 'Text 1', 'http://example.com/photo1.jpg', datetime.now())
    print(db.read_all_records())
    db.update_active_status(1, 0)
    print(db.get_last_id())
    db.close()
