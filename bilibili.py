import requests
import time
from utils import contains_substring
from database import check_id_exists, insert_data

def get_at(conn, cur):
    cookie = {}  # 设置cookie,填自己账号的
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
            while num < items_length:
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
                    get_at(conn, cur)

                if check_id_exists(cur, 'id', item_id):
                    print("因为数据存在,所以重新查询")
                    get_at(conn, cur)

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
                        get_at(conn, cur)

                else:
                    print("这个数组的内容不是交卷,继续查询")

                num += 1
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
