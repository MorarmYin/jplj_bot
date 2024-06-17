from database import open_database, close_database, create_table
from bilibili import get_at

def start_get_at():
    conn, cur = open_database('BilibiliData.db')
    print("数据库连接成功")
    create_table(conn, cur)
    get_at(conn, cur)
    close_database(conn)
