import sqlite3
from datetime import datetime, timezone

def open_database(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    return connection, cursor

def close_database(connection):
    connection.close()

def create_table(conn, cur):
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bilibili_items (
        id INTEGER PRIMARY KEY,
        at_time TEXT,
        user_nickname TEXT,
        user_avatar TEXT,
        item_type TEXT,
        item_title TEXT,
        item_uri TEXT
    )
    ''')
    conn.commit()

def check_id_exists(cur, column_name, value):
    query = f"SELECT EXISTS(SELECT 1 FROM bilibili_items WHERE {column_name} = ?)"
    cur.execute(query, (value,))
    exists = cur.fetchone()[0]
    return exists

def insert_data(conn, cur, item):
    at_time = datetime.fromtimestamp(
        item["at_time"], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('''
        INSERT INTO bilibili_items (id, at_time, user_nickname, user_avatar, item_type, item_title, item_uri)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (item["id"], at_time, item["user"]["nickname"], item["user"]["avatar"],
              item["item"]["type"], item["item"]["title"], item["item"]["uri"]))
    conn.commit()
