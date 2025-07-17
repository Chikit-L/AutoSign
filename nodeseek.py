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
import time
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# ========== 环境变量 ==========
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
SIGN_MODE = os.environ.get("NS_SIGN_MODE", "chicken")  # chicken / lucky
COOKIE = os.environ.get("NS_COOKIE2")
SCREENSHOT_DIR = "/ql/data/photo"

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

def setup_browser():
    """初始化浏览器并设置 Cookie"""
    if not COOKIE:
        print("❌ 环境变量中未找到 COOKIE，请设置 NS_COOKIE 或 COOKIE")
        return None

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    if HEADLESS:
        print("✅ 启用无头模式")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
        )

    #driver = uc.Chrome(options=chrome_options)
    driver = uc.Chrome(
        options=chrome_options,
        driver_executable_path='/usr/bin/chromedriver',
        version_main=138
    )

    # 隐藏自动化特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
    })

    print("🌐 正在访问 nodeseek.com...")
    try:
        driver.get("https://www.nodeseek.com")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("🎉 页面加载成功")
    except Exception as e:
        print(f"❌ 页面加载失败: {str(e)}")
        return None

    # 添加 Cookie
    for item in COOKIE.split(";"):
        try:
            name, value = item.strip().split("=", 1)
            driver.add_cookie({
                "name": name,
                "value": value,
                "domain": ".nodeseek.com",
                "path": "/",
            })
        except Exception as e:
            print(f"⚠️ 添加 Cookie 失败: {e}")
            continue

    print("🔄 刷新页面以应用 Cookie...")
    try:
        driver.refresh()
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("🎉 页面刷新成功")
    except Exception as e:
        print(f"❌ 页面刷新失败: {str(e)}")
        return None

    time.sleep(5)

    # 验证是否登录成功并获取用户名
    try:
        username_element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.Username"))
        )
        username = username_element.text.strip()
        print(f"🔐 登录成功，当前账号为: {username}")
    except Exception as e:
        print("❌ 未检测到用户名元素，可能登录失败或 Cookie 无效")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"login_failure_{timestamp}.png")
            driver.save_screenshot(screenshot_path)
            print(f"📸 已保存登录失败截图：{screenshot_path}")
        except Exception as screen_error:
            print(f"⚠️ 截图保存失败: {str(screen_error)}")
        return None

    return driver

def click_sign_icon(driver):
    """点击首页的签到图标"""
    try:
        sign_icon = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@title='签到']"))
        )
        sign_icon.click()
        print("🎉 签到图标点击成功")
        return True
    except Exception as e:
        print(f"❌ 点击签到图标失败: {str(e)}")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"sign_in_failure_{timestamp}.png")
            driver.save_screenshot(screenshot_path)
            print(f"📸 签到失败截图已保存至: {screenshot_path}")
        except Exception as screen_error:
            print(f"⚠️ 截图保存失败: {str(screen_error)}")
        return False

def check_sign_status(driver):
    """检查签到状态：通过是否有 button 来判断是否已签到"""
    try:
        driver.get("https://www.nodeseek.com/board")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 定位 head-info 区域
        head_info_div = driver.find_element(By.CSS_SELECTOR, ".head-info > div")

        # 检查是否有 button 存在
        buttons = head_info_div.find_elements(By.TAG_NAME, "button")
        if buttons:
            print("🔄 今日尚未签到")
            return False  # 尚未签到
        else:
            sign_info = head_info_div.text.strip()
            print(f"✅ 今日已签到: {sign_info}")
            return True   # 已签到

    except Exception as e:
        print(f"❌ 检查签到状态失败: {str(e)}")
        return False
        
def click_sign_button(driver):
    """查找并点击签到按钮，兼容已签到情况"""
    try:
        print("🔍 开始查找签到区域...")

        # 检查是否已签到
        already_signed = driver.find_elements(By.XPATH, "//div[contains(., '今日已签到')]")
        if already_signed:
            print("✅ 今日已签到")
            return True

        # 查找签到按钮容器
        sign_div = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[button[text()='鸡腿 x 5'] and button[text()='试试手气']]"
            ))
        )
        print("✅ 找到签到区域")

        # 根据 SIGN_MODE 决定点击哪个按钮
        if SIGN_MODE == "chicken":
            print("🍗 准备点击「鸡腿 x 5」按钮")
            button = sign_div.find_element(By.XPATH, ".//button[text()='鸡腿 x 5']")
        elif SIGN_MODE == "lucky":
            print("🎲 准备点击「试试手气」按钮")
            button = sign_div.find_element(By.XPATH, ".//button[text()='试试手气']")
        else:
            print(f"❌ 未知的签到模式: {SIGN_MODE}，请设置 chicken 或 lucky")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5)
        button.click()
        print("🎉 按钮点击成功！签到完成")
        return True

    except Exception as e:
        print(f"❌ 签到过程中出错: {str(e)}")
        print(traceback.format_exc())

        # 输出当前页面信息用于调试
        print("📄 当前页面 URL:", driver.current_url)
        print("📄 页面源码片段:\n", driver.page_source[:1000])
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"sign_in_failure_{timestamp}.png")
            driver.save_screenshot(screenshot_path)
            print(f"📸 已保存错误截图：{screenshot_path}")
        except:
            pass

        return False

if __name__ == "__main__":
    print("🚀 开始执行 NodeSeek 签到脚本...")

    driver = setup_browser()
    if not driver:
        print("🚫 浏览器初始化失败")
        exit(1)

    try:
        if not click_sign_icon(driver):
            print("🚫 点击签到图标失败")
            exit(1)

        is_signed = check_sign_status(driver)
        if is_signed:
            print("✅ 今日已签到，无需重复操作。任务结束。")
            exit(0)

        result = click_sign_button(driver)
        if result:
            print("✅ 签到成功！")
        else:
            print("❌ 签到失败")
    finally:
        print("🛑 脚本执行完毕，关闭浏览器")
        driver.quit()
