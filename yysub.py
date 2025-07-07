#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("人人字幕组签到")

import os
import requests
import time
from notify import send  # 导入通知函数

# 请求用户信息的URL
url = "https://www.yysub.vip/user/login/getCurUserTopInfo"

# 获取环境变量中的 cookie
def get_cookie():
    return os.getenv('yysub_cookie', '')

# 发起GET请求获取用户数据
def get_user_info(retry_count=3):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'cookie': get_cookie(),
    }

    while retry_count > 0:
        try:
            response = requests.get(url, headers=headers)

            # 如果请求成功，解析响应
            if response.status_code == 200:
                data = response.json()
                # 提取需要的信息
                nickname = data['data']['userinfo']['nickname']
                cont_login = data['data']['usercount']['cont_login']
                message = f"用户 {nickname} 已连续登陆 {cont_login} 天"
                print(message)
                return message  # 成功时返回消息

            else:
                print(f"请求失败，状态码: {response.status_code}")

        except Exception as e:
            print(f"发生错误: {str(e)}")

        retry_count -= 1
        if retry_count > 0:
            print(f"重试中... 剩余重试次数: {retry_count}")
            time.sleep(2)  # 等待2秒后重试

    return None  # 如果重试次数用尽，返回 None

# 执行签到操作
if __name__ == "__main__":
    result_message = get_user_info()

    # 根据结果发送不同的通知
    if result_message:
        send("人人字幕组签到成功", result_message)  # 成功时发送签到结果
    else:
        send("人人字幕组签到失败", "签到失败，无法获取用户信息。")  # 失败时发送简单失败消息
