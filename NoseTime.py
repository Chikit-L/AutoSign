#!/usr/bin/env bash
# cron:30 9 * * *
# new Env("香水时代")
# 抓包 https://app.nosetime.com/app/user.php 中 id 用于获取用户的基本信息。
# https://app.nosetime.com/app/points.php?uid=xxxxxxx 中 token
# 填入环境变量 Nosetime ： id#token

import requests
import json
import os
from sendNotify import send  # 导入通知功能

def sign_in():
    url = "https://app.nosetime.com/app/user.php"
    headers = {
        "Host": "app.nosetime.com",
        "Content-Length": "42",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; MI 9 Build/RKQ1.200826.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.0.4758.101 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://localhost",
        "X-Requested-With": "com.nosetime.perfume",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://localhost/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    # 从环境变量中获取 Nosetime
    nosetime_env = os.getenv("Nosetime")
    if not nosetime_env:
        print("未找到所需的 Nosetime 环境变量")
        return

    # 分割 id 和 token
    try:
        user_id, token = nosetime_env.split("#")
    except ValueError:
        print("Nosetime 环境变量格式错误，应为 'id#token'")
        return

    # 第一个请求 - 获取用户信息
    payload = {
        "method": "getsocialinfo",
        "id": user_id
    }
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            # 解析第一个请求的 JSON 响应
            data = response.json()
            uname = data.get("uname", "未知用户")
            ulevel = data.get("ulevel", "未知等级")
            ulevelstr = data.get("ulevelstr", "未知称号")
            
            # 生成签到信息
            sign_in_message = f"{uname}签到成功，目前等级lv{ulevel}，称号<{ulevelstr}>"
            print(sign_in_message)
            
            # 发起第二个请求 - 增加积分
            second_url = f"https://app.nosetime.com/app/points.php?uid={user_id}"
            second_payload = {
                "method": "increasetip",
                "token": token
            }
            
            second_response = requests.post(second_url, headers=headers, json=second_payload)
            
            if second_response.status_code == 200:
                second_data = second_response.json()
                msg = second_data.get("msg", "").replace("“", "").replace("”", "")
                
                # 检查积分请求的响应内容
                if msg:
                    points_message = f"今日{msg}"
                else:
                    points_message = f"{uname}今日已签到，目前等级lv{ulevel}，称号<{ulevelstr}>"
                
                print(points_message)
                
                # 发送通知
                send(title="签到结果", content=f"{sign_in_message}\n{points_message}")
            else:
                print(f"积分增加请求失败，状态码: {second_response.status_code}, 响应内容: {second_response.text}")
        
        except json.JSONDecodeError:
            print("响应解析失败，返回数据不是有效的JSON格式")
    else:
        print(f"获取用户信息失败，状态码: {response.status_code}, 响应内容: {response.text}")

# 执行签到
sign_in()

