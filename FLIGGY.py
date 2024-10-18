#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("飞猪签到")

import hashlib
import time
import json
import requests
import os

# 从环境变量获取 Cookie
FLIGGY_COOKIE = os.getenv("FLIGGY_COOKIE")  # 青龙面板配置环境变量 FLIGGY_COOKIE

# 从 Cookie 中提取 _m_h5_tk 和其他必要参数
def extract_token_and_cookie(cookie):
    try:
        _m_h5_tk = cookie.split('_m_h5_tk=')[1].split(';')[0]
        token = _m_h5_tk.split('_')[0]
        return token, cookie
    except Exception as e:
        print("无法从 Cookie 中提取 token，请检查 Cookie 格式:", e)
        exit(1)

# 生成签名 sign
def generate_sign(token, t, appKey, data_str):
    raw_string = f"{token}&{t}&{appKey}&{data_str}"
    md5 = hashlib.md5()
    md5.update(raw_string.encode("utf-8"))
    return md5.hexdigest()

# 执行签到请求
def sign_in():
    # 请求相关参数
    appKey = "12574478"
    token, cookie = extract_token_and_cookie(FLIGGY_COOKIE)
    t = str(int(time.time() * 1000))  # 时间戳

    # 请求数据
    request_data = {
        "taoCash": False,
        "doubleMileage": False,
        "channel": "LX",
        "sceneId": 722,
        "clickType": 2,
        "playId": "sign1824",
        "taskRecordId": None,
        "currentTimeMillis": int(time.time() * 1000),
        "currentMileage": 135,
        "h5Version": "1.0.23"
    }
    data_str = json.dumps(request_data)

    # 生成签名
    sign = generate_sign(token, t, appKey, data_str)

    # 请求参数
    params = {
        "type": "originaljsonp",
        "api": "mtop.fliggy.ffatouch.mileage.channel.v2024.clickcollect",
        "v": "1.0",
        "data": data_str,
        "needLogin": "true",
        "responseType": "ORIGINAL_JSON",
        "ttid": "201300@travel_h5_3.1.0",
        "appKey": appKey,
        "t": t,
        "sign": sign,
        "callback": "mtop_cback_320530106_9"
    }

    # 发送请求
    url = "https://h5api.m.taobao.com/h5/mtop.fliggy.ffatouch.mileage.channel.v2024.clickcollect/1.0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": cookie,
        "Origin": "https://outfliggys.m.taobao.com",
        "Referer": "https://outfliggys.m.taobao.com/app/trip/rx-mileage2024/pages/home"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

        # 判断签到结果
        if result.get("ret", [])[0].startswith("SUCCESS"):
            mileage = result["data"]["clickCollectSignInResult"]["result"]["resultData"]["awards"][0]["awardSendDetail"]["resourceGroupDTOS"][0]["rightGroupDTOS"][0]["rightDTOS"][0]["faceValueDTO"]["rightCopies"]
            print(f"签到成功！获得里程 {mileage} 里程")
        else:
            print("签到失败:", result.get("ret", [])[0])
    except requests.exceptions.RequestException as e:
        print("请求失败:", e)

# 主程序入口
if __name__ == "__main__":
    sign_in()
