# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz
# @Time   : 2025-09-01
# NodeLoc 签到脚本
# -------------------------------
"""
NodeLoc签到
自行网页捉包提取请求头中的cookie和x-csrf-token填到变量 NLCookie 中,用#号拼接，多账号换行隔开
export NL_COOKIE="_t=******; _forum_session=xxxxxx#XXXXXX"

cron: 59 8 * * *
const $ = new Env("NodeLoc签到");
"""
import os
import time
import logging
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ==================== 固定配置 ====================
DOMAIN = "www.nodeloc.com"
HOME_URL = f"https://{DOMAIN}/u/"  # 用户列表页
CHECKIN_BUTTON_SELECTOR = 'li.header-dropdown-toggle.checkin-icon button.checkin-button'
USERNAME_SELECTOR = 'div.directory-table__row.me a[data-user-card]'  # 当前登录用户
SCREENSHOT_DIR = "/ql/data/photo"
LOG_LEVEL = logging.INFO
# =================================================
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

results = []

def generate_screenshot_path(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return os.path.join(SCREENSHOT_DIR, f"{prefix}_{ts}.png")

def get_username_from_user_page(driver) -> str:
    log.debug("🔍 正在提取用户名...")
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, USERNAME_SELECTOR))
        )
        username = element.get_attribute("data-user-card")
        return username.strip() if username else "未知用户"
    except Exception as e:
        log.error(f"❌ 提取用户名失败: {e}")
        return "未知用户"

def check_login_status(driver):
    log.debug("🔐 正在检测登录状态...")
    try:
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.directory-table__row.me")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.checkin-button"))
            )
        )
        log.info("✅ 登录成功")
        return True
    except Exception as e:
        log.error(f"❌ 登录失败或 Cookie 无效: {e}")
        screenshot_path = generate_screenshot_path('login_failed')
        driver.save_screenshot(screenshot_path)
        log.info(f"📸 已保存登录失败截图：{screenshot_path}")
        return False

def setup_browser():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--headless=new')
    log.debug("🌐 启动 Chrome（无头模式）...")
    try:
        driver = uc.Chrome(
            options=options,
            driver_executable_path='/usr/bin/chromedriver',
            version_main=138,
            use_subprocess=True
        )
        driver.set_window_size(1920, 1080)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        driver.execute_script("window.chrome = { runtime: {} };")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});")

        return driver
    except Exception as e:
        log.error(f"❌ 浏览器启动失败: {e}")
        return None

def hover_checkin_button(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CHECKIN_BUTTON_SELECTOR)))
        ActionChains(driver).move_to_element(button).perform()
        time.sleep(1)
    except Exception as e:
        log.warning(f"⚠️ 刷新签到状态失败: {e}")

def perform_checkin(driver, username: str):
    try:
        driver.get("https://www.nodeloc.com/")
        time.sleep(3)
        hover_checkin_button(driver)
        wait = WebDriverWait(driver, 10)
        button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CHECKIN_BUTTON_SELECTOR)))

        if "checked-in" in button.get_attribute("class"):
            msg = f"[✅] {username} 今日已签到"
            log.info(msg)
            return msg

        log.info(f"📌 {username} - 准备签到")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)

        hover_checkin_button(driver)

        if "checked-in" in button.get_attribute("class"):
            msg = f"[🎉] {username} 签到成功！"
            log.info(msg)
            return msg
        else:
            msg = f"[⚠️] {username} 点击后状态未更新，可能失败"
            log.warning(msg)
            path = generate_screenshot_path("checkin_uncertain")
            driver.save_screenshot(path)
            log.info(f"📸 已保存状态存疑截图：{path}")
            return msg

    except Exception as e:
        msg = f"[❌] {username} 签到异常: {e}"
        log.error(msg)
        path = generate_screenshot_path("checkin_error")
        try:
            driver.save_screenshot(path)
            log.info(f"📸 已保存错误截图：{path}")
        except:
            pass
        return msg

def process_account(cookie_str: str):
    cookie = cookie_str.split("#", 1)[0].strip()
    if not cookie:
        log.error("❌ Cookie 为空")
        return "[❌] Cookie 为空"

    driver = None
    try:
        driver = setup_browser()
        if not driver:
            return "[❌] 浏览器启动失败"

        log.info("🚀 正在打开用户列表页...")
        driver.get(HOME_URL)
        time.sleep(3)

        log.debug("🍪 正在设置 Cookie...")
        for item in cookie.split(";"):
            item = item.strip()
            if not item or "=" not in item:
                continue
            try:
                name, value = item.split("=", 1)
                driver.add_cookie({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.nodeloc.com',
                    'path': '/',
                    'secure': True,
                    'httpOnly': False
                })
            except Exception as e:
                log.warning(f"[⚠️] 添加 Cookie 失败: {item} -> {e}")
                continue

        driver.refresh()
        time.sleep(5)

        if not check_login_status(driver):
            return "[❌] 登录失败，Cookie 可能失效"

        username = get_username_from_user_page(driver)
        log.info(f"👤 当前用户: {username}")

        result = perform_checkin(driver, username)
        return result

    except Exception as e:
        msg = f"[🔥] 处理异常: {e}"
        log.error(msg)
        return msg
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    global results
    if 'NL_COOKIE' not in os.environ:
        msg = "❌ 未设置 NL_COOKIE 环境变量"
        print(msg)
        results.append(msg)
        return

    raw_lines = os.environ.get("NL_COOKIE").strip().split("\n")
    cookies = [line.strip() for line in raw_lines if line.strip()]

    if not cookies:
        msg = "❌ 未解析到有效 Cookie"
        print(msg)
        results.append(msg)
        return

    log.info(f"✅ 查找到 {len(cookies)} 个账号，开始顺序签到...")

    for cookie_str in cookies:
        result = process_account(cookie_str)
        results.append(result)
        time.sleep(5)

    log.info("✅ 全部签到完成")

if __name__ == '__main__':
    main()
