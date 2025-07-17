# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz https://github.com/wh1te3zzz/checkin
# @Time : 2025-07-16 15:42:16
# NodeSeek签到脚本
# -------------------------------
"""
NodeSeek签到
自行网页捉包提取请求头中的cookie填到变量 NS_COOKIE 中
export NS_COOKIE="XXXXXX"

cron: 30 8 * * *
const $ = new Env("NodeSeek签到");
"""
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback
import undetected_chromedriver as uc

ns_random = os.environ.get("NS_RANDOM","false")
cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
# 通过环境变量控制是否使用无头模式，默认为 True（无头模式）
headless = os.environ.get("HEADLESS", "true").lower() == "true"

def click_sign_icon(driver):
    """
    尝试点击签到图标和试试手气按钮的通用方法
    """
    try:
        print("开始查找签到图标...")
        sign_icon = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//span[@title='签到']"))
        )
        print("找到签到图标，准备点击...")
        
        driver.execute_script("arguments[0].scrollIntoView(true);", sign_icon)
        time.sleep(0.5)
        
        try:
            sign_icon.click()
            print("签到图标点击成功")
        except Exception as click_error:
            print(f"点击失败，尝试使用 JavaScript 点击: {str(click_error)}")
            driver.execute_script("arguments[0].click();", sign_icon)
        
        print("等待页面跳转...")
        time.sleep(5)
        
        print(f"当前页面URL: {driver.current_url}")
        
        try:
            if ns_random:
                click_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '试试手气')]"))
            )
            else:
                click_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '鸡腿 x 5')]"))
            )
            
            click_button.click()
            print("完成试试手气点击")
        except Exception as lucky_error:
            print(f"试试手气按钮点击失败或者签到过了: {str(lucky_error)}")
            
        return True
        
    except Exception as e:
        print(f"签到过程中出错:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"当前页面URL: {driver.current_url}")
        print(f"当前页面源码片段: {driver.page_source[:500]}...")
        print("详细错误信息:")
        traceback.print_exc()
        return False

def setup_driver_and_cookies():
    """
    初始化浏览器并设置cookie的通用方法
    返回: 设置好cookie的driver实例
    """
    try:
        cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
        headless = os.environ.get("HEADLESS", "true").lower() == "true"
        
        if not cookie:
            print("未找到cookie配置")
            return None
            
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        #driver = uc.Chrome(options=options)
        driver = uc.Chrome(
            options=options,
            driver_executable_path='/usr/bin/chromedriver',
            version_main=138
        )
        
        if headless:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(1920, 1080)
        
        driver.get('https://www.nodeseek.com')
        
        time.sleep(5)
        
        for cookie_item in cookie.split(';'):
            try:
                name, value = cookie_item.strip().split('=', 1)
                driver.add_cookie({
                    'name': name, 
                    'value': value, 
                    'domain': '.nodeseek.com',
                    'path': '/'
                })
            except Exception as e:
                print(f"设置cookie出错: {str(e)}")
                continue
        
        driver.refresh()
        time.sleep(5)  
        
        return driver
        
    except Exception as e:
        print(f"设置浏览器和Cookie时出错: {str(e)}")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print("开始执行NodeSeek签到脚本...")
    driver = setup_driver_and_cookies()
    if not driver:
        print("浏览器初始化失败")
        exit(1)
    click_sign_icon(driver)
    print("脚本执行完成")
