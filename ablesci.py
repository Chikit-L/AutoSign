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
from cachetools import cached, TTLCache
import datetime


def get_headers(cookie: str) -> Dict[str, str]:
    # 动态生成最新浏览器UA
    def generate_user_agent(platform: str) -> str:
        # 生成随机版本号（主版本从120到125，保持更新）
        major_version = random.randint(120, 125)
        minor_version = random.randint(0, 10)
        build_version = random.randint(2000, 9999)
        
        # 桌面端UA模板
        desktop_templates = [
            f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.{minor_version}.{build_version} Safari/537.36',
            f'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{major_version}.0) Gecko/20100101 Firefox/{major_version}.0',
            f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36 Edg/{major_version}.0.{minor_version}.{build_version}'
        ]
        
        # 移动端UA模板
        mobile_templates = [
            f'Mozilla/5.0 (iPhone; CPU iPhone OS 17_{random.randint(1,5)} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1',
            f'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Mobile Safari/537.36'
        ]
        
        # 根据平台选择模板
        if platform == 'desktop':
            return random.choice(desktop_templates)
        return random.choice(mobile_templates)
    
    # 随机选择平台类型
    is_mobile = random.choice([True, False])
    user_agent = generate_user_agent('mobile' if is_mobile else 'desktop')
    
    # 带异常处理的版本提取
    try:
        chrome_match = re.search(r'Chrome/(\d+\.\d+\.\d+\.\d+)', user_agent)
        chrome_version = chrome_match.group(1) if chrome_match else '125.0.0.0'
        # 同步Edge版本处理
        edge_match = re.search(r'Edg/(\d+\.\d+\.\d+\.\d+)', user_agent)
        edge_version = edge_match.group(1) if edge_match else f'{chrome_version.split(".")[0]}.0.0.0'
    except Exception as e:
        print(f"Chrome版本提取失败: {str(e)}")
        chrome_version = '125.0.0.0'
    
    edge_version = chrome_version.split('.')[0] + '.0.0.0'  # 统一使用Chrome主版本
    
    # 生成随机XFF头
    x_forwarded_for = f'{random.randint(60, 220)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}'
    
    headers = {
        'authority': 'www.ablesci.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'cookie': cookie,
        'dnt': str(random.randint(0, 1)),  # 随机DNT标识
        'pragma': 'no-cache',
        'referer': 'https://www.ablesci.com/',
        'sec-ch-ua': f'"Chromium";v="{chrome_version.split(".")[0]}", "Microsoft Edge";v="{edge_version.split(".")[0]}", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '["Windows", "Linux", "macOS"][random.randint(0,2)]',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': user_agent,
        'x-requested-with': 'XMLHttpRequest',
        'x-forwarded-for': x_forwarded_for,
        'x-real-ip': x_forwarded_for
    }
    
    # 随机化headers顺序
    keys = list(headers.keys())
    random.shuffle(keys)
    
    return {k: headers[k] for k in keys}


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


# 缓存配置（1小时更新）
ua_cache = TTLCache(maxsize=100, ttl=3600)

@cached(ua_cache)
def generate_user_agent(platform: str) -> str:
    # 生成随机版本号（主版本从120到最新）
    current_year = datetime.datetime.now().year
    major_version = random.randint(120, current_year - 2010 + 120)
    # 增加Firefox和Edge版本生成
    browser_type = random.choice(['chrome', 'firefox', 'edge'])
    
    # 动态模板库
    templates = {
        'desktop': {
            'chrome': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36',
            'firefox': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{major_version}.0) Gecko/20100101 Firefox/{major_version}.0',
            'edge': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36 Edg/{major_version}.0.0.0'
        },
        'mobile': {
            'chrome': f'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Mobile Safari/537.36',
            'firefox': f'Mozilla/5.0 (Android 13; Mobile; rv:{major_version}.0) Gecko/{major_version}.0 Firefox/{major_version}.0',
            'edge': f'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Mobile Safari/537.36 EdgA/{major_version}.0.0.0'
        }
    }
    
    try:
        return templates[platform][browser_type]
    except Exception as e:
        print(f"UA生成失败: {str(e)}")
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'


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