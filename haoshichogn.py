#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("好时充签到")


import os
import requests
import json

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

            # 输出签到结果
            print(f"签到成功！\n今天签到获得 {gain} 积分，总积分为 {processed}分")
        else:
            print("签到失败，返回信息:", result)
    else:
        print("签到请求失败，状态码：", response.status_code)

except Exception as e:
    print("请求过程中出现错误：", str(e))
