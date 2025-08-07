#!/usr/bin/env python
# cron:40 7,21 * * *
# new Env("科研通签到")
# coding=utf-8

"""
AbleSci自动签到脚本 - 多账号版
创建日期：2025年8月8日
作者：daitcl
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
import json

# 检测运行环境
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
IS_QINGLONG = not IS_GITHUB_ACTIONS

# 设置环境变量名称
ENV_ACCOUNTS = "ABLESCI_ACCOUNTS"  # 多账号环境变量

# 消息通知系统
class Notifier:
    def __init__(self):
        self.log_content = []
        self.title = "科研通签到"
        self.notify_enabled = False
        
        # 在所有环境尝试导入通知模块
        try:
            # 添加当前目录到系统路径确保能导入
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from sendNotify import send
            self.send = send
            self.notify_enabled = True
        except ImportError:
            # 在 GitHub Actions 中可能路径不同
            try:
                # 尝试从父目录导入
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                sys.path.append(parent_dir)
                from sendNotify import send
                self.send = send
                self.notify_enabled = True
            except Exception as e:
                self.log(f"导入通知模块失败: {str(e)}", "warning")
                self.notify_enabled = False
    
    def log(self, message, level="info"):
        """格式化日志输出并保存到内容"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        level_map = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }
        symbol = level_map.get(level, "ℹ️")
        log_message = f"[{timestamp}] {symbol} {message}"
        print(log_message)
        self.log_content.append(log_message)
        
    def send_notification(self):
        """发送通知"""
        if not self.notify_enabled:
            self.log("通知功能未启用", "warning")
            return False
            
        content = "\n".join(self.log_content)
        
        try:
            self.send(self.title, content)
            self.log("通知发送成功", "success")
            return True
        except Exception as e:
            self.log(f"发送通知失败: {str(e)}", "error")
            return False
    
    def get_content(self):
        """获取日志内容"""
        return "\n".join(self.log_content)

class AbleSciAuto:
    def __init__(self, email, password):
        self.session = requests.Session()
        self.email = email
        self.password = password
        self.username = None  # 存储用户名
        self.points = None    # 存储当前积分
        self.sign_days = None # 存储连续签到天数
        self.notifier = Notifier()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.start_time = time.time()
        # self.notifier.log(f"处理账号: {self.email}", "info")
        self.notifier.log(f"运行环境: {'GitHub Actions' if IS_GITHUB_ACTIONS else '青龙面板'}", "info")
        
    def log(self, message, level="info"):
        """代理日志到通知系统"""
        self.notifier.log(message, level)
        
    def get_csrf_token(self):
        """获取CSRF令牌"""
        login_url = "https://www.ablesci.com/site/login"
        try:
            response = self.session.get(login_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_token = soup.find('input', {'name': '_csrf'})
                if csrf_token:
                    return csrf_token.get('value', '')
            else:
                self.log(f"获取CSRF令牌失败，状态码: {response.status_code}", "error")
        except Exception as e:
            self.log(f"获取CSRF令牌时出错: {str(e)}", "error")
        return ''

    def login(self):
        """执行登录操作"""
        if not self.email or not self.password:
            self.log("邮箱或密码为空", "error")
            return False
            
        login_url = "https://www.ablesci.com/site/login"
        csrf_token = self.get_csrf_token()
        
        if not csrf_token:
            self.log("无法获取CSRF令牌", "error")
            return False
        
        login_data = {
            "_csrf": csrf_token,
            "email": self.email,
            "password": self.password,
            "remember": "off"
        }
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["Referer"] = "https://www.ablesci.com/site/login"
        
        try:
            response = self.session.post(
                login_url,
                data=login_data,
                headers=headers,
                timeout=30
            )
            
            # 检查登录结果
            if response.status_code == 200:
                try:
                    # 尝试解析JSON响应
                    result = response.json()
                    if result.get("code") == 0:
                        self.log(f"登录成功: {result.get('msg')}", "success")
                        return True
                    else:
                        self.log(f"登录失败: {result.get('msg')}", "error")
                except json.JSONDecodeError:
                    # 如果不是JSON，可能是HTML响应
                    if "退出" in response.text:  # 检查登录成功标志
                        self.log("登录成功", "success")
                        return True
                    else:
                        self.log("登录失败: 无法解析响应", "error")
            else:
                self.log(f"登录请求失败，状态码: {response.status_code}", "error")
        except Exception as e:
            self.log(f"登录过程中出错: {str(e)}", "error")
        return False

    def get_user_info(self):
        """获取用户信息（包括用户名、积分和签到天数）"""
        # 访问首页（登录后通常会显示用户名）
        home_url = "https://www.ablesci.com/"
        headers = self.headers.copy()
        headers["Referer"] = "https://www.ablesci.com/"
        
        try:
            response = self.session.get(home_url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 1. 获取用户名
                username_element = soup.select_one('.mobile-hide.able-head-user-vip-username')
                if username_element:
                    self.username = username_element.text.strip()
                    self.log(f"用户名: {self.username}", "info")
                else:
                    self.log("无法定位用户名元素", "warning")
                
                # 2. 获取积分信息
                points_element = soup.select_one('#user-point-now')
                if points_element:
                    self.points = points_element.text.strip()
                    self.log(f"当前积分: {self.points}", "info")
                else:
                    self.log("无法获取积分信息", "warning")
                
                # 3. 获取连续签到天数
                sign_days_element = soup.select_one('#sign-count')
                if sign_days_element:
                    self.sign_days = sign_days_element.text.strip()
                    self.log(f"连续签到天数: {self.sign_days}", "info")
                else:
                    self.log("无法获取连续签到天数", "warning")
                
                return True
            else:
                self.log(f"获取首页失败，状态码: {response.status_code}", "error")
        except Exception as e:
            self.log(f"获取用户信息时出错: {str(e)}", "error")
        return False

    def sign_in(self):
        """执行签到操作 - 修复已签到处理"""
        sign_url = "https://www.ablesci.com/user/sign"
        headers = self.headers.copy()
        headers["Referer"] = "https://www.ablesci.com/"
        
        try:
            response = self.session.get(sign_url, headers=headers, timeout=30)
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("code") == 0:
                        self.log(f"签到成功: {result.get('msg')}", "success")
                        
                        # 尝试从响应中获取新的积分和签到天数
                        data = result.get("data", {})
                        if data:
                            if "points" in data:
                                self.points = data["points"]
                                self.log(f"更新积分: {self.points}", "info")
                            if "sign_days" in data:
                                self.sign_days = data["sign_days"]
                                self.log(f"更新连续签到天数: {self.sign_days}", "info")
                        
                        return True
                    else:
                        msg = result.get('msg', '')
                        # 特殊处理已签到情况
                        if "已经签到" in msg or "已签到" in msg:
                            self.log(f"今日已签到: {msg}", "info")
                            return True
                        else:
                            self.log(f"签到失败: {msg}", "error")
                except json.JSONDecodeError:
                    self.log("签到响应不是有效的JSON", "error")
            else:
                self.log(f"签到请求失败，状态码: {response.status_code}", "error")
        except Exception as e:
            self.log(f"签到过程中出错: {str(e)}", "error")
        return False

    def display_summary(self):
        """显示执行摘要"""
        elapsed = round(time.time() - self.start_time, 2)
        self.log("=" * 50)
        self.log(f"用户 {self.username} 执行摘要:")
        if self.username:
            self.log(f"  • 用户名: {self.username}")
        if self.points:
            self.log(f"  • 当前积分: {self.points}")
        if self.sign_days:
            self.log(f"  • 连续签到: {self.sign_days}天")
        self.log(f"  • 执行耗时: {elapsed}秒")
        self.log("=" * 50)
        
        # 添加额外空行
        self.log("")
        self.log("")

    def run(self):
        """执行完整的登录和签到流程"""
        if self.login():
            self.get_user_info()
            # 直接执行签到，不检查状态
            self.sign_in()
        
        self.display_summary()
        
        # 返回日志内容，供主程序汇总
        return self.notifier.get_content()

def get_accounts():
    """从环境变量获取所有账号"""
    accounts_env = os.getenv(ENV_ACCOUNTS)
    if not accounts_env:
        return []
    
    accounts = []
    # 支持多种分隔符：换行符、分号、逗号
    for line in accounts_env.splitlines():
        # 跳过空行
        if not line.strip():
            continue
            
        # 支持分号和逗号分隔的多个账号
        if ";" in line:
            accounts.extend(line.split(";"))
        elif "," in line:
            accounts.extend(line.split(","))
        else:
            accounts.append(line)
    
    # 验证账号格式并分离邮箱密码
    valid_accounts = []
    for account in accounts:
        # 支持邮箱和密码用冒号、分号或竖线分隔
        if ":" in account:
            email, password = account.split(":", 1)
        elif ";" in account:
            email, password = account.split(";", 1)
        elif "|" in account:
            email, password = account.split("|", 1)
        else:
            continue  # 跳过格式不正确的账号
            
        email = email.strip()
        password = password.strip()
        
        if email and password:
            valid_accounts.append((email, password))
    
    return valid_accounts

def main():
    """主函数，处理多账号签到"""
    # 创建全局通知器
    global_notifier = Notifier()
    global_notifier.log("科研通多账号签到任务开始", "info")
    
    # 获取所有账号
    accounts = get_accounts()
    account_count = len(accounts)
    
    if account_count == 0:
        global_notifier.log("未找到有效的账号配置", "error")
        global_notifier.log(f"请设置环境变量 {ENV_ACCOUNTS}，格式为：邮箱1:密码1[换行]邮箱2:密码2", "warning")
        if global_notifier.notify_enabled:
            global_notifier.send_notification()
        return
    
    global_notifier.log(f"找到 {account_count} 个账号", "info")
    
    # 执行每个账号的签到任务
    all_logs = []
    for i, (email, password) in enumerate(accounts, 1):
        global_notifier.log(f"\n===== 开始处理第 {i}/{account_count} 个账号 =====", "info")
        
        # 创建并执行签到实例
        automator = AbleSciAuto(email, password)
        account_log = automator.run()
        all_logs.append(account_log)
        
        # 添加分隔符
        global_notifier.log(f"===== 完成第 {i}/{account_count} 个账号处理 =====", "info")
    
    # 汇总所有日志
    global_notifier.log("\n===== 所有账号处理完成 =====", "info")
    full_log = "\n\n".join(all_logs)
    
    # 发送汇总通知
    if global_notifier.notify_enabled:
        # 创建新通知器用于发送汇总通知
        summary_notifier = Notifier()
        summary_notifier.log_content = full_log.splitlines()
        summary_notifier.send_notification()
    
    # 在GitHub Actions环境中输出日志内容
    if IS_GITHUB_ACTIONS:
        print(f"::set-output name=log_content::{full_log}")

if __name__ == "__main__":
    main()