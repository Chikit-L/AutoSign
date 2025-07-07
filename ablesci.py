#!/usr/bin/env python
# cron:40 7,21 * * *
# new Env("科研通签到")
# coding=utf-8

# 标准库导入
import os
import re
import random
import time
import datetime
from typing import Dict, Any, Iterator

# 第三方库导入
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cachetools import cached, TTLCache

# 本地模块导入
from sendNotify import send  # 消息通知模块


def generate_interval() -> float:
    """生成1-5秒随机请求间隔"""
    return random.uniform(1, 5)

# 缓存配置（1小时更新）
ua_cache = TTLCache(maxsize=100, ttl=3600)

@cached(ua_cache)
def generate_user_agent(platform: str) -> str:
    """
    生成随机用户代理字符串(User-Agent)

    功能特性:
    - 支持生成桌面版/移动版双平台UA头
    - 动态生成Chrome主版本号（基于当前年份计算）
    - 支持Chrome/Firefox/Edge三大浏览器类型
    - 内置1小时缓存机制避免重复生成

    参数:
        platform (str): 平台类型，'desktop' 或 'mobile'

    返回值:
        str: 符合现代浏览器特征的随机User-Agent字符串

    实现细节:
        1. Chrome版本号生成规则:
           - 基准版本: 120
           - 动态增量: (当前年份 - 2010)
           - 最终版本范围: 120 ~ (当前年份 - 2010 + 120)
        2. 浏览器类型随机选择Chrome/Firefox/Edge
        3. 使用TTLCache实现1小时缓存，避免频繁生成

    异常处理:
        - 捕获所有异常并返回备用UA
        - 打印异常信息便于调试
    """
    templates = {
        "desktop": {
            "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36",
            "firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{major_version}.0) Gecko/20100101 Firefox/{major_version}.0",
            "edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36 Edg/{major_version}.0.0.0"
        },
        "mobile": {
            "chrome": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Mobile Safari/537.36",
            "firefox": "Mozilla/5.0 (Android 13; Mobile; rv:{major_version}.0) Gecko/{major_version}.0 Firefox/{major_version}.0",
            "edge": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Mobile Safari/537.36 EdgA/{major_version}.0.0.0"
        }
    }
    try:
        current_year = datetime.datetime.now().year
        major_version = random.randint(120, current_year - 2010 + 120)
        
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
        
        browser_type = random.choice(['chrome', 'firefox', 'edge'])
        return templates[platform][browser_type]
    except Exception as e:
        print(f"UA生成异常: {str(e)}")
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'



def get_headers(cookie: str) -> Dict[str, str]:
    is_mobile = random.choice([True, False])
    user_agent = generate_user_agent('mobile' if is_mobile else 'desktop')

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
    """
    创建带重试机制的HTTP会话

    参数:
        retries: 最大重试次数，默认3次

    特性:
        - 对500/502/503/504状态码自动重试
        - 使用指数退避策略（退避因子0.5）
        - 适配HTTP/HTTPS协议

    返回:
        requests.Session: 配置好的会话对象
    """
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
    - 必须设置ABLESCICOOKIE环境变量
    - 支持两种格式（可混合使用）：
        1. 带前缀格式：cookie数字=真实cookie内容（如cookie1=security_session_verify=xxx）
        2. 原始格式：完整cookie字符串（如security_session_verify=xxx; other_cookie=yyy）
    - 多个账号配置需用换行符分隔

    解析规则:
    - 使用正则表达式r'^(cookie\\d+=)?(.+?)$'匹配条目
    - 分组1捕获前缀（可选），分组2捕获实际cookie内容
    - 自动去除两端空白字符，跳过空行
    - 支持包含等号(=)和分号(;)的复杂cookie格式

    返回值:
        Iterator[str]: 生成器，按顺序返回解析后的有效cookie字符串

    异常处理:
    - 环境变量未设置时输出红色错误信息
    - 格式错误条目会记录警告日志并跳过
    - 自动过滤包含非法字符或结构错误的条目
    - 返回的cookie字符串已去除两端空白字符
    """
    cookie_env = os.environ.get('ABLESCICOOKIE', '')
    if not cookie_env.strip():
        print("\033[31m[严重错误] 环境变量ABLESCICOOKIE未设置或为空！\033[0m")
        return
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
            print(f"[警告] Cookie格式错误: {entry}")


def extract_chinese(html_content: str) -> str:
    """
    从HTML内容提取中文字段

    参数:
        html_content: 原始HTML字符串

    处理流程:
        1. 匹配所有<p>和<div>标签内容
        2. 清除残留HTML标签
        3. 保留中文字符、数字及常用标点（，。！？等）
        4. 过滤空段落并用换行符连接

    返回:
        str: 整理后的纯文本内容，段落间用换行分隔

    异常:
        返回空字符串并打印错误日志
    """
    try:  
        # 匹配所有<p>标签内容
        paragraphs = re.findall(r'<(?:p|div)[^>]*>(.*?)</(?:p|div)>', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # 对每个段落单独处理
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5\d，。！？；：、（）《》【】「」“”‘’—…a-zA-Z.]+')
        cleaned_paragraphs = [
            ''.join(chinese_pattern.findall(re.sub(r'<[^>]+>', '', p)))
            for p in paragraphs
        ]
        
        # 用换行符连接有效段落
        return '\n'.join([p for p in cleaned_paragraphs if p])
    
    except Exception as e:
        print(f'处理失败：{str(e)}')
        return ''


if __name__ == "__main__":
    content = "="*26 + "\n"
    cookies_found = False
    for cookie in cookies():
        if not cookie:
            continue
        cookies_found = True

        interval = generate_interval()
        time.sleep(interval)

        result = ablesci(cookie)
        profile = ablesci_index(cookie)

        content += f"{profile}今日科研通签到:\n{result.get('msg', '')}\n"

        if result.get('code') == 0:
            content += extract_chinese(f"{result['data']['today_history']}")+ "\n"
        else:
            print("签到失败")

        time.sleep(interval)

    if not cookies_found:
        content += "\033[31m[错误] 未找到任何有效的cookie配置，请检查环境变量ABLESCICOOKIE是否正确设置\033[0m\n"
    
    content += "="*26
    print(content)
    send("科研通签到", content)