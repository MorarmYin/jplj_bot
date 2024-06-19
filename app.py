from flask import Flask, render_template, request,send_from_directory
from flask_socketio import SocketIO
import threading
import signal
import sys
import os
from database import open_database, close_database
from get_at_thread import start_get_at
from utils import create_dir

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)  # 默认页码为 1
    per_page = request.args.get('per_page', 20, type=int)  # 默认每页显示 10 条记录
    conn, cur = open_database('BilibiliData.db')
    # 计算跳过的记录数
    offset = (page - 1) * per_page
    # 修改查询以实现分页
    cur.execute("SELECT * FROM bilibili_items LIMIT ? OFFSET ?", (per_page, offset))
    rows = cur.fetchall()
    # 获取总记录数
    cur.execute("SELECT COUNT(*) FROM bilibili_items")
    total = cur.fetchone()[0]
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    close_database(conn)
    # 返回分页数据和分页信息
    return render_template('index.html', rows=rows, page=page, per_page=per_page, total=total, total_pages=total_pages)

@app.route('/avatar')
def avatar():
    filename = request.args.get('filename')  # 假设查询参数名为filename
    directory = os.path.join(app.root_path, 'imgs')  # 假设图片存储在项目根目录下的img文件夹
    return send_from_directory(directory, filename, mimetype='image/jpeg')

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    socketio.stop()
    sys.exit(0)

if __name__ == "__main__":
    create_dir()
    signal.signal(signal.SIGINT, signal_handler)
    thread = threading.Thread(target=start_get_at)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
