import requests
import json
import sqlite3
import time
from datetime import datetime, timezone
from flask import Flask, render_template, send_file, request
from io import BytesIO
from threading import Thread, Event
import signal
import sys

app = Flask(__name__)

def contains_substring(main_string, sub_string):
    return sub_string in main_string

def check_id_exists(cur, column_name, value):
    query = f"SELECT EXISTS(SELECT 1 FROM bilibili_items WHERE {column_name} = ?)"
    cur.execute(query, (value,))
    exists = cur.fetchone()[0]
    return exists

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

def insert_data(conn, cur, item):
    at_time = datetime.fromtimestamp(
        item["at_time"], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('''
        INSERT INTO bilibili_items (id, at_time, user_nickname, user_avatar, item_type, item_title, item_uri)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (item["id"], at_time, item["user"]["nickname"], item["user"]["avatar"],
              item["item"]["type"], item["item"]["title"], item["item"]["uri"]))
    conn.commit()

def get_at(stop_event, conn, cur):
    cookie = {}  # 设置cookie,填自己账号的
    while not stop_event.is_set():
        print("开始查询")
        time.sleep(15)
        num = 0
        response = requests.get(
            "https://api.bilibili.com/x/msgfeed/at?build=0&mobi_app=web", headers=cookie)
        data = response.json()

        if data['code'] == 0:
            print("连接api成功！")
            while not stop_event.is_set():
                if num >= len(data['data']['items']):
                    break
                item = data['data']['items'][num]
                user_nickname = item['user']['nickname']
                item_id = item['id']
                item_type = item['item']['type']
                item_title = item['item']['title']
                item_uri = item['item']['uri']
                item_source_content = item['item']['source_content']
                item_target_id = item['item']['target_id']

                print(f"{user_nickname}艾特了机器人")

                if item_source_content == "":
                    print("这个数组的内容是空的(?),重新查询")
                    break

                if check_id_exists(cur, 'id', item_id):
                    print("因为数据存在,所以重新查询")
                    break

                print("这条数据不在数据库,继续执行")

                if item_target_id != 0:
                    at_content_end = item_title
                else:
                    at_content_end = item_source_content

                if contains_substring(at_content_end, '交卷'):
                    reply_type = item['item']['business_id']
                    oid = item['item']['subject_id']
                    root = item['item']['source_id']
                    csrf = "92b45b3455cbd959963d8d36b50e103c"
                    at_content_name = user_nickname

                    if check_id_exists(cur, 'item_uri', item_uri):
                        reply_content = "交卷收到！已有人提交过此视频！"
                    else:
                        reply_content = f"视频交卷成功！视频名称：{item_title}，提交人：{at_content_name}"
                        insert_data(conn, cur, item)

                    if send_reply(reply_type, oid, root, reply_content, csrf, cookie) != 0:
                        print("发送消息失败")
                        break

                    num += 1
                else:
                    print("这个数组的内容不是交卷,继续查询")
                    num += 1
        else:
            print("连接api失败，请检查cookie")

def send_reply(reply_type, oid, root, reply_content, csrf, cookie):
    reply_data = {
        "oid": oid,
        "type": reply_type,
        "root": root,
        "parent": root,
        "message": reply_content,
        "plat": "1",
        "ordering": "time",
        "jsonp": "jsonp",
        "csrf": csrf
    }
    time.sleep(1)
    response = requests.post("https://api.bilibili.com/x/v2/reply/add", headers=cookie, data=reply_data)
    return response.json()['code']

@app.route('/')
def index():
    conn, cur = open_database('BilibiliData.db')
    cur.execute("SELECT * FROM bilibili_items")
    rows = cur.fetchall()
    close_database(conn)
    return render_template('index.html', rows=rows)

@app.route('/avatar')
def avatar():
    url = request.args.get('url')
    response = requests.get(url)
    return send_file(BytesIO(response.content), mimetype='image/jpeg')

def signal_handler(signal, frame, stop_event):
    print("捕捉到中断信号，正在退出...")
    stop_event.set()

def main():
    stop_event = Event()
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, stop_event))

    conn, cur = open_database('BilibiliData.db')
    print("数据库连接成功")
    create_table(conn, cur)

    # 启动获取@消息的功能
    thread = Thread(target=get_at, args=(stop_event, conn, cur))
    thread.start()

    # 启动Flask Web应用
    app.run(debug=True, use_reloader=False)

    thread.join()
    close_database(conn)

if __name__ == "__main__":
    main()
