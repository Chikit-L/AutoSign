#!/usr/bin/env bash
# cron:0 8 * * *
# new Env("雨晨ios资源自动签到")

import os
import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from notify import send  # Import the send function from notify.py

# 配置日志记录
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

name = "雨晨ios资源"


class YuChen:
    """处理账号信息"""

    def __init__(self):
        # 从环境变量中获取账号、密码和用户代理
        self.username = os.getenv('YUCHEN_USERNAME')
        self.password = os.getenv('YUCHEN_PASSWORD')
        self.user_agent = os.getenv('YUCHEN_USER_AGENT', "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0")
        self.session = requests.session()
        self.cookie = None
        self.token = self.get_token()
        log.debug(self.__str__())

    def __str__(self):
        return f'username={self.username}, password={self.password}, user_agent={self.user_agent}'

    def headers(self):
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "yc.yuchengyouxi..com",
            "Origin": "https://yc.yuchengyouxi..com",
            "User-Agent": self.user_agent
        }

    def get_token(self) -> str:
        """
        获取登录所需token
        """
        url = "https://yc.yuchengyouxi..com/login"
        headers = {
            "User-Agent": self.user_agent
        }
        response = self.session.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find('input', {'name': 'token'}).get('value')
        log.debug(f"token:{token}")
        return token

    def yuchen_login(self):
        """
        登录网站
        """
        url = "https://yc.yuchengyouxi.com/wp-admin/admin-ajax.php"
        data = {
            "user_login": self.username,
            "password": self.password,
            "rememberme": "1",
            "redirect": "https://yc.yuchengyouxi..com/",
            "action": "userlogin_form",
            "token": self.token
        }
        headers = self.headers()
        response = self.session.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = self.login_result_handler(response.json())
        if message['success'] == "error":
            log.info("登录失败")
            log.info(message['msg'])
            return False
        return True

    def yuchen_check(self):
        """
        签到
        """
        url = "https://yc.yuchengyouxi..com/wp-admin/admin-ajax.php"
        data = {
            "action": "daily_sign"
        }
        headers = self.headers()
        response = self.session.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = self.login_result_handler(response.json())
        log.info(message['msg'])
        return message['msg']  # 返回签到结果

    def yuchen_info(self):
        """
        获取积分总值
        """
        url = "https://yc.yuchengyouxi..com/users?tab=credit"
        headers = self.headers()
        response = self.session.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.find('div', {'class': 'header_tips'}).text
        log.info(text)
        return text  # 返回积分信息

    def yuchen_sign(self):
        """判断账号信息是否完整"""
        if not self.username or not self.password or not self.user_agent:
            log.info("账号信息不完整，跳过此账号")
            return False
        return True

    def run(self):
        """运行"""
        is_a = self.yuchen_login()
        if is_a:
            sign_result = self.yuchen_check()
            credit_info = self.yuchen_info()
            return sign_result, credit_info
        return None, None

    def login_result_handler(self, response_json):
        """
        处理登录结果的简易函数
        """
        return response_json


def sleep_random():
    """随机暂停一段时间，模拟人为操作"""
    sleep_time = random.randint(1, 10)
    log.info(f"随机暂停 {sleep_time} 秒")
    time.sleep(sleep_time)


def main():
    log.info(f"{name}开始签到")
    yuchen = YuChen()
    if yuchen.yuchen_sign():
        try:
            sign_result, credit_info = yuchen.run()
            if sign_result and credit_info:
                # 签到成功后推送信息
                message = f"签到结果: {sign_result}\n积分信息: {credit_info}"
                send(f"{name}签到成功", message)  # Use notify.py's send function
        except Exception as e:
            log.info(f"签到失败: {e}")
            send(f"{name}签到失败", str(e))  # Use notify.py's send function
        sleep_random()


if __name__ == '__main__':
    main()
