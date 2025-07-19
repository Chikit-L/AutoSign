# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz https://github.com/wh1te3zzz/checkin
# @Time : 2025-05-22 10:06:56
# NodeLoc签到脚本
# -------------------------------
"""
NodeLoc签到
自行网页捉包提取请求头中的cookie和x-csrf-token填到变量 NLCookie 中,用#号拼接，多账号换行隔开
export NL_COOKIE="_t=******; _forum_session=xxxxxx#XXXXXX"

cron: 59 8 * * *
const $ = new Env("NodeLoc签到");
"""
import os
import re
import requests
from notify import send
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait

# 分割变量：解析 NLCookie 环境变量
if 'NL_COOKIE' in os.environ:
    lines = os.environ.get("NL_COOKIE").strip().split("\n")
    NLCookie = []
    for line in lines:
        parts = line.strip().split("#", 1)  # 最多分割一次
        if len(parts) == 2:
            cookie, token = parts
            NLCookie.append({
                "cookie": cookie,
                "x-csrf-token": token
            })
    print(f'查找到{len(NLCookie)}个账号')
else:
    NLCookie = [{
        "cookie": "",
        "x-csrf-token": ""
    }]
    print('无NLCookie变量')

URL = "https://nodeloc.cc/checkin"
results = []  # 用于存储签到结果

def sign_in(account):
    ck = account["cookie"]
    token = account["x-csrf-token"]

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "discourse-logged-in": "true",
        "discourse-present": "true",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-csrf-token": token,
        "x-requested-with": "XMLHttpRequest",
        "cookie": ck,
        "Referer": "https://nodeloc.cc/",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

    try:
        response = requests.post(URL, headers=headers, timeout=30)
        if response.status_code == 200:
            username = response.headers.get('x-discourse-username', '未知用户')
            try:
                result = response.json()
                if result.get("success"):
                    points = result.get('points', '未知')
                    msg = f"[✅] {username} 签到成功！获得{points}能量！"
                    print(msg)
                else:
                    message = result.get("message", "未知错误")
                    msg = f"[✅] {username} 签到成功！{message}！"
                    print(msg)
                results.append(msg)
            except requests.exceptions.JSONDecodeError:
                msg = f"[⚠️] {username} 签到成功但响应不是 JSON 格式。"
                results.append(msg)
                print(msg)
                print(response.text[:200])
        else:
            msg = f"[❌] 签到失败，状态码：{response.status_code}"
            results.append(msg)
            print(msg)
            print(response.text[:200])
    except Exception as e:
        msg = f'[🔥] 请求过程中出错：{e}'
        results.append(msg)
        print(msg)

def main():
    global results
    print("开始批量签到...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(sign_in, account) for account in NLCookie]
        wait(futures)
    print("全部签到完成")
    # 拼接通知内容
    if results:
        all_content = "\n".join(results)
        send(title="NodeLoc 签到", content=all_content)
    else:
        send(title="NodeLoc 签到", content="未检测到签到结果，请检查配置。")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error_msg = f'[ERROR] 主程序运行时出现错误: {e}'
        print(error_msg)
        send(title="NodeLoc 签到异常", content=error_msg)
