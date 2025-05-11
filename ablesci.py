#!/usr/bin/env python
# cron:40 7,21 * * *
# new Env("科研通签到")
# coding=utf-8
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from sendNotify import send
import re
import random
import time
from typing import Optional, Dict, Any, List, Iterator


def get_headers(cookie: str) -> Dict[str, str]:
    return {
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


def create_session(retries: int = 3) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def ablesci(cookie: str) -> Dict[str, Any]:
    url = "https://www.ablesci.com/user/sign"
    session = create_session()
    try:
        response = session.get(url, headers=get_headers(cookie), timeout=10)
        response.raise_for_status()
        print("成功访问签到接口")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        return {'code': -1, 'msg': '网络请求失败'}


def ablesci_index(cookie: str) -> str:
    url = "https://www.ablesci.com/my/home"
    session = create_session()
    try:
        response = session.get(url, headers=get_headers(cookie), timeout=10)
        response.raise_for_status()
        html = response.text

        links = re.findall(r'<title.*?>(.+?)</title>', html)
        links2 = re.findall(r'<span style="color: #FF7200;.*?>(.+?)</span>', html)
        return f"{''.join(links)}{''.join(links2)}\n"
    except requests.exceptions.RequestException as e:
        print(f"主页请求失败: {str(e)}")
        return ""


def cookies() -> Iterator[str]:
    """
    从环境变量解析科研通多账号cookie配置

    环境变量要求:
    - 使用ABLESCICOOKIE环境变量存储多个cookie
    - 支持两种格式：
        1. cookie数字=真实cookie内容（如cookie1=x1234...）
        2. 原始cookie格式（如security_session_verify=值; other_cookie=值）
    - 多个配置间用换行符分隔

    返回值:
        Iterator[str]: 生成器，逐个返回有效cookie字符串

    异常处理:
    - 自动跳过空行和无效格式条目
    - 使用正则表达式r'^(cookie\\d+=)?(.+?)$'匹配带前缀和不带前缀的cookie
    - 无效条目会记录warning级别日志
    """
    import re
    import logging
    cookie_env = os.environ.get('ABLESCICOOKIE', '')
    cookies = cookie_env.splitlines()
    pattern = re.compile(r'^(cookie\d+=)?(.+?)$', re.MULTILINE)
    
    for entry in cookies:
        entry = entry.strip()
        if not entry:
            continue
        match = pattern.search(entry)
        if match:
            # 提取分组2的内容（原始cookie）或分组1（无前缀时整个匹配）
            yield match.group(2).strip() if match.group(2) else match.group(1).strip()
        else:
            logging.warning(f"Invalid cookie format: {entry}")


def generate_interval(base: float = 60.0) -> float:
    return random.uniform(0, base)


if __name__ == "__main__":
    content = "="*26 + "\n"
    for cookie in cookies():
        if not cookie:
            continue

        interval = generate_interval()
        time.sleep(interval)

        result = ablesci(cookie)
        profile = ablesci_index(cookie)

        content += f"{profile}今日科研通签到:\n{result.get('msg', '')}\n"

        if result.get('code') == 0:
            content += f"{result['data']['today_history']}\n"
        else:
            print("签到失败")

        time.sleep(interval)

    content += "="*26
    print(content)
    send("科研通签到", content)