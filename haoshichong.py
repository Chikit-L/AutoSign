#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("好时充签到")


import os
import requests
import json
import time
import sys

# Import the notify.py
from notify import send  # Import send function

# 请求的 URL
url = 'http://user.123sunny.com/Wechat.php/Client/UserInfo/checkin'

# 从环境变量中获取好时充签到的 Cookie
cookie = os.getenv('HSC_COOKIE')

# 使用安卓的 User-Agent 模拟签到请求
headers = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate',
    'Origin': 'http://user.123sunny.com',
    'Cookie': cookie,  # 使用从环境变量获取的 HSC_COOKIE
    'Connection': 'keep-alive',
    'Host': 'user.123sunny.com',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36',  # 安卓设备的 User-Agent
    'Referer': 'http://user.123sunny.com/Wechat.php',
    'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
    'X-Requested-With': 'XMLHttpRequest'
}

# 请求体（此处为空）
data = {}

# 最大重试次数
max_retries = 3
retry_count = 0

# 最终的消息变量，用于在最后推送
final_message = ""

while retry_count < max_retries:
    try:
        # 发起 POST 请求
        response = requests.post(url, headers=headers, data=data)

        # 检查响应状态码
        if response.status_code == 200:
            # 解析响应体
            result = json.loads(response.text)
            if result.get('success'):
                gain = result['score']['gain']  # 今天获得的积分
                processed = result['score']['processed']  # 总积分

                # 构建最终成功消息
                final_message = f"签到成功！\n今天签到获得 {gain} 积分，总积分为 {processed}分"
                print(final_message)
                break  # 签到成功，退出循环
            else:
                final_message = f"签到失败，返回信息: {result}"
                print(final_message)
        else:
            final_message = f"签到请求失败，状态码：{response.status_code}"
            print(final_message)

    except Exception as e:
        final_message = f"请求过程中出现错误：{str(e)}"
        print(final_message)

    # 增加重试次数
    retry_count += 1

    if retry_count > max_retries:
        # 等待 30 秒后重试，不推送重试信息
        print(f"重试 {retry_count}/{max_retries}，等待 30 秒后再次尝试...")
        time.sleep(30)
    else:
        final_message = "已达到最大重试次数，签到失败。"
        print(final_message)

# 仅在最后推送最终的签到结果
if final_message:
    send("好时充签到", final_message)
