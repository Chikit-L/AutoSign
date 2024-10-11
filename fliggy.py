#!/usr/bin/env bash
# cron:0 8 * * *
# new Env("飞猪里程签到")

import os
import time
import random
import logging
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从环境变量中获取用户名和密码
username = os.getenv("FLIGGY_USERNAME")
password = os.getenv("FLIGGY_PASSWORD")

# 最初的里程中心页面链接
mileage_page_url = "https://outfliggys.m.taobao.com/app/trip/rx-mileage2024/pages/home?disableNav=YES&titleBarHidden=2&__webview_options__=fullscreen%3DYES&spm=181.29007744.0.0&pre_pageVersion=1.0.44&fpt=ftuid(pv9s5IVT176286.2)&_projVer=1.0.22"

def random_sleep(min_time=1, max_time=3):
    """在 min_time 和 max_time 之间随机等待时间，模拟用户的随机行为"""
    time.sleep(random.uniform(min_time, max_time))

def human_type(element, text):
    """逐个字符输入，模拟人类打字"""
    for char in text:
        element.send_keys(char)
        random_sleep(0.1, 0.3)  # 每个字符输入间隔随机

def sign_in_fliggy():
    try:
        # 查找 chromedriver 路径
        chromedriver_path = shutil.which("chromedriver")
        if not chromedriver_path:
            logging.error("未找到 chromedriver，请确保它已安装并在 PATH 中。")
            return False

        # 配置 Chrome 的无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")

        # 反检测Selenium
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 启动浏览器
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)


        # 修改navigator.webdriver属性以避免检测
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        # 打开里程中心页面
        driver.get(mileage_page_url)

        # 随机延迟以模拟页面加载
        random_sleep(3, 5)

        # 切换帐号密码登陆
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="login-form"]/div[6]/a'))
            )
            element.click()
            logging.info("点击帐号密码登录成功")
        except Exception as e:
            logging.error(f"点击失败: {e}")
            return False

        # 输入用户名
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="fm-login-id"]'))
            )
            username_field.clear()
            human_type(username_field, username)
            logging.info("用户名输入成功")
        except TimeoutException:
            logging.error("用户名输入框没有在指定时间内出现。")
            return False
        except Exception as e:
            logging.error(f"输入用户名失败: {e}")
            return False

        # 随机延迟以模拟打字的自然行为
        random_sleep(1, 2)

        # 输入密码
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="fm-login-password"]'))
            )
            password_field.clear()
            human_type(password_field, password)
            logging.info("密码输入成功")
        except TimeoutException:
            logging.error("密码输入框没有在指定时间内出现。")
            return False
        except Exception as e:
            logging.error(f"输入密码失败: {e}")
            return False

        # 同意协议
        try:
            label = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//label[@for="fm-agreement-checkbox"]'))
            )
            
            # 确保目标元素没有被其他元素遮挡
            driver.execute_script("arguments[0].scrollIntoView(true);", label)
            random_sleep(0.5, 1)  # 等待片刻

            # 使用 JavaScript 点击
            driver.execute_script("arguments[0].click();", label)
            logging.info("同意协议成功")
        except Exception as e:
            logging.error(f"点击同意协议失败: {e}")
            return False


        # 随机延迟模拟用户思考
        random_sleep(2, 4)

        # 点击登录按钮
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and contains(@class, "fm-submit")]'))
            )
            driver.execute_script("arguments[0].click();", login_button)
            logging.info("登录按钮点击成功，登录中...")
        except TimeoutException:
            logging.error("登录按钮没有在指定时间内出现。")
            return False
        except Exception as e:
            logging.error(f"点击登录按钮失败: {e}")
            return False

        logging.info("登录完成，准备执行任务")

        # 调用任务处理函数
        return complete_task(driver)

    except WebDriverException as e:
        logging.error(f"WebDriver 错误: {e}")
        return False
    except Exception as e:
        logging.error(f"出现错误: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

def complete_task(driver):
    try:
        # 添加等待时间，确保页面完全加载
        random_sleep(10, 12)

        # 使用组合选择器定位签到按钮
        sign_in_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//div[contains(@class, "sign-center-center") and contains(@data-spm-abcd, "sign_oldman")]'))
        )

        # 使用JavaScript执行点击
        driver.execute_script("arguments[0].click();", sign_in_button)
        logging.info("签到按钮点击成功，正在完成签到...")

        # 等待5秒后再次点击，以确保点击成功
        random_sleep(5, 6)
        driver.execute_script("arguments[0].click();", sign_in_button)
        logging.info("再次点击签到按钮，确保签到成功...")
        return True

    except TimeoutException:
        logging.error("签到按钮没有在指定时间内出现，可能加载时间较长或未加载。")
        return False
    except Exception as e:
        logging.error(f"点击签到按钮失败: {e}")
        return False

# 重试逻辑，最多重试3次
def retry_sign_in(retry_count=3):
    attempt = 0
    while attempt < retry_count:
        logging.info(f"开始第 {attempt + 1} 次尝试...")
        if sign_in_fliggy():
            logging.info("签到成功！")
            return True
        else:
            logging.info("本次签到失败，等待30秒后重试...")
            time.sleep(30)
            attempt += 1
    logging.error("全部尝试均失败，签到失败。")
    return False

# 执行签到流程，最多重试三次
retry_sign_in()
