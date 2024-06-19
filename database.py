import sqlite3
from datetime import datetime, timezone, timedelta

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
        at_user_id TEXT,
        at_user_nickname TEXT,
        item_title TEXT,
        item_uri TEXT,
        BVID TEXT,
        owner_id TEXT,
        owner_nickname TEXT,
        pass_time TEXT
    )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS at_id (
            id INTEGER PRIMARY KEY
        )
        ''')
    conn.commit()

def check_id_exists(cur, table_name, column_name, value):
    query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {column_name} = ?)"
    cur.execute(query, (value,))
    exists = cur.fetchone()[0]
    return exists

def delete_row_by_id(conn, cur, item):
    cur.execute(f"DELETE FROM at_id WHERE id = ?", (item["id"],))
    conn.commit()

def insert_at_data(conn, cur, item, video_item):
    at_time = datetime.fromtimestamp(item["at_time"], tz=timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    pass_time = datetime.fromtimestamp(video_item["ctime"], tz=timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('''
        INSERT INTO bilibili_items (id, at_time, at_user_id, at_user_nickname, item_title, item_uri, BVID, owner_id, owner_nickname, pass_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item["id"], at_time, item["user"]["mid"],item["user"]["nickname"], item["item"]["title"], item["item"]["uri"],video_item["bvid"], video_item["owner"]["mid"], video_item["owner"]["name"], pass_time))
    conn.commit()

def insert_at_id(conn, cur, item):
    cur.execute('''
        INSERT INTO at_id (id)
        VALUES (?)
        ''', (item["id"],))
    conn.commit()