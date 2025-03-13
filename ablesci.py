#!/usr/bin/env python
# cron:40 7,21 * * *
# new Env("科研通签到")
# coding=utf-8
import requests
import os
from sendNotify import send
import re
import random
import time

def ablesci(cookie):
    url = "https://www.ablesci.com/user/sign"
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cookie': cookie,
        'dnt': '1',
        'priority': 'u=1, i',
        'referer': 'https://www.ablesci.com/',
        'sec-ch-ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
    }
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        print("成功访问")
    return response.json()

def ablesci_index(cookie):
    url = "https://www.ablesci.com/my/home"
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cookie': cookie,
        'dnt': '1',
        'priority': 'u=1, i',
        'referer': 'https://www.ablesci.com/',
        'sec-ch-ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
    }
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        html=response.text
    links = re.findall(r'<title.*?>(.+?)</title>',html)
    links2 = re.findall(r'<span style="color: #FF7200;.*?>(.+?)</span>',html)
    str1 = ''.join(links)
    str2 = ''.join(links2)
    return str1 + str2 + "\n"


def cookies():
    cookie = os.environ.get('ABLESCICOOKIE')
    cookie2 = cookie.split("\n")
    return cookie2
    
if __name__ == "__main__":
    content = "==========================\n"
    for cookie1 in cookies():
        interval = random.uniform(0, 60)
        msg =  ablesci(cookie1)
        time.sleep(interval)
        content += ablesci_index(cookie1)
        content += "今日科研通签到: \n" + msg['msg'] + "\n"
        code = msg['code']
        if code == 0:
          content += msg['data']['today_history'] + "\n"
        else :
          print("签到失败")
        time.sleep(interval)
    content += "=========================="
    print(content)
    send("科研通签到", content)
    

