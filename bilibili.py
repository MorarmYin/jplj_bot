import requests
import time
from utils import contains_substring
from database import check_id_exists, delete_row_by_id, insert_at_data, insert_at_id
import config

def get_at(conn, cur):
    while True:
        print("开始查询")
        time.sleep(15)
        num = 0
        response = requests.get(
            "https://api.bilibili.com/x/msgfeed/at?build=0&mobi_app=web", headers=config.cookie)
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
                business_id= item['item']['business_id']
                at_time = item['at_time']
                print(f"{user_nickname}艾特了机器人")

                if item_source_content == "":
                    print("这个数组的内容是空的(?),重新查询")
                    get_at(conn, cur)

                if check_id_exists(cur, 'at_id', 'id', item_id):
                    print("因为数据存在,所以重新查询")
                    get_at(conn, cur)

                insert_at_id(conn, cur, item)
                print("这条数据不在数据库,继续执行")

                if business_id == 1 and contains_substring(item_source_content, '交卷'):
                    reply_type = item['item']['business_id']
                    oid = item['item']['subject_id']
                    root = item['item']['source_id']
                    at_content_name = user_nickname

                    if check_id_exists(cur, 'bilibili_items', 'item_uri', item_uri):
                        reply_content = "交卷收到！已有人提交过此视频！"
                    else:
                        reply_content = f"视频交卷成功！视频名称：{item_title}，提交人：{at_content_name}"
                        bvid = item["item"]["uri"].split("/")[-1]
                        time.sleep(1)
                        video_response = requests.get('https://api.bilibili.com/x/web-interface/view', params={'bvid': bvid},headers=config.cookie)
                        video_data = video_response.json()
                        if video_data['code'] == 0:
                            video_item = video_data['data']
                            insert_at_data(conn, cur, item, video_item)
                        else:
                            print("获取视频信息失败")
                            delete_row_by_id(conn, cur, item)
                            get_at(conn, cur)

                    if send_reply(reply_type, oid, root, reply_content, config.cookie) != 0:
                    #if 0 != 0: #测试用
                        print("发送消息失败")
                        delete_row_by_id(conn, cur, item)
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
        "csrf": config.csrf
    }
    response = requests.post("https://api.bilibili.com/x/v2/reply/add", headers=cookie, data=reply_data)
    return response.json()['code']
