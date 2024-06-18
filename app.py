from flask import Flask, render_template, send_file, request
from flask_socketio import SocketIO
from io import BytesIO
import threading
import signal
import sys

import requests
from database import open_database, close_database
from get_at_thread import start_get_at

app = Flask(__name__)
socketio = SocketIO(app)

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

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    socketio.stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    thread = threading.Thread(target=start_get_at)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
