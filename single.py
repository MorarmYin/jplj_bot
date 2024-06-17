import requests
import json
import sqlite3
import time
from datetime import datetime, timezone
from flask import Flask, render_template, send_file, request
from flask_socketio import SocketIO
from io import BytesIO
import threading
import signal
import sys

app = Flask(__name__)
socketio = SocketIO(app)

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

def get_at(conn, cur):
    cookie = {'Cookie':'buvid3=DA5E65D2-9728-FE43-D9EC-467F55044E8873342infoc; b_nut=1718599573; b_lsid=16D94E49_19024846E8B; _uuid=1DD104D92-952A-6C4F-5566-7B63FC5C6D10177234infoc; buvid4=74FF5528-63DF-6BE3-F226-6668C255C4BE73947-024061704-5RGJE%2B6NJDbDAqPsLgQGCA%3D%3D; buvid_fp=9730a0f648b28b5b2a004d4ed0c89b5d; enable_web_push=DISABLE; header_theme_version=undefined; home_feed_column=5; browser_resolution=1536-776; SESSDATA=535f69ee%2C1734151590%2C43c28%2A62CjBDreZgGx7BpXUJ-n1D8UqXR6jjVldFZPRBBr6-3QH3EpgGGKJgOimT8h4ohXXFPu8SVmdwWWdZQ3JIZnRWd0ZiT1ZHa1JIYS04YTVILS1tUllnZDJIU0ZVdV96dWFFMklrcUtnNDA3cjV5YXNDdldmWktNWFF5UEtPWXJ6U3dXLVdvMDYxSWFnIIEC; bili_jct=4960dbdee2b87a4c8e7b6add2fdc4f31; DedeUserID=1409036162; DedeUserID__ckMd5=80213c09bddfe4e4; sid=p76ye1r2; bp_t_offset_1409036162=943851378629935104; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTg4NTg3OTYsImlhdCI6MTcxODU5OTUzNiwicGx0IjotMX0.sB7lvYWNLGi4ok0DLPsbrRpoyq41ZfT3rY0jgLPfGew; bili_ticket_expires=1718858736',
              'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}  # 设置cookie,填自己账号的
    while True:
        print("开始查询")
        time.sleep(15)
        num = 0
        response = requests.get(
            "https://api.bilibili.com/x/msgfeed/at?build=0&mobi_app=web", headers=cookie)
        data = response.json()

        if data['code'] == 0:
            print("连接api成功！")
            items = data['data']['items']
            items_length = len(items)
            while num < items_length:  # 添加越界检查
                item = items[num]
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
                    get_at(conn,cur)

                if check_id_exists(cur, 'id', item_id):
                    print("因为数据存在,所以重新查询")
                    get_at(conn,cur)

                print("这条数据不在数据库,继续执行")

                if item_target_id != 0:
                    at_content_end = item_title
                else:
                    at_content_end = item_source_content

                if contains_substring(at_content_end, '交卷'):
                    reply_type = item['item']['business_id']
                    oid = item['item']['subject_id']
                    root = item['item']['source_id']
                    at_content_name = user_nickname

                    if check_id_exists(cur, 'item_uri', item_uri):
                        reply_content = "交卷收到！已有人提交过此视频！"
                    else:
                        reply_content = f"视频交卷成功！视频名称：{item_title}，提交人：{at_content_name}"
                        insert_data(conn, cur, item)

                    if send_reply(reply_type, oid, root, reply_content, cookie) != 0:
                        print("发送消息失败")
                        get_at(conn,cur)

                else:
                    print("这个数组的内容不是交卷,继续查询")

                num += 1  # 增加num，确保在while循环内继续检查下一个item
        else:
            print("连接api失败，请检查cookie")

def send_reply(reply_type, oid, root, reply_content, cookie):
    reply_data = {
        "oid": oid,
        "type": reply_type,
        "root": root,
        "parent": root,
        "message": reply_content,
        "plat": "1",
        "ordering": "time",
        "jsonp": "jsonp",
        "csrf": '4960dbdee2b87a4c8e7b6add2fdc4f31'
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

def start_get_at():
    conn, cur = open_database('BilibiliData.db')
    print("数据库连接成功")
    create_table(conn, cur)
    get_at(conn, cur)
    close_database(conn)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    socketio.stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    thread = threading.Thread(target=start_get_at)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
