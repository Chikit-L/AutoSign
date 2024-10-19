#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("卡饭签到")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import logging
import shutil
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from notify import send  # 引入 send 函数用于发送消息

# 初始化日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# 获取青龙面板中的账号和密码环境变量，格式为: '帐号;密码'
credentials = os.getenv('KAFAN')
if not credentials or ';' not in credentials:
    logging.error("未检测到正确格式的环境变量 KAFAN")
    exit(1)

# 拆分账号和密码
account, password = credentials.split(';')

# 检查 chromedriver 是否存在
chromedriver_path = shutil.which("chromedriver")
if not chromedriver_path:
    logging.error("chromedriver 未找到，请确保已安装并配置正确的路径")
    exit(1)

# 初始化 WebDriver，使用无头模式
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")  # 无头模式，注释掉这行可以看到浏览器操作
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = None

try:
    logging.info("启动 Selenium WebDriver")
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

    # 访问卡饭论坛
    logging.info("访问卡饭论坛")
    driver.get('https://bbs.kafan.cn/')
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="comeing_toptb"]')))
    time.sleep(3)  # 增加页面加载等待时间

    # 点击“快速登陆”
    login_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="comeing_toptb"]/div/div[2]/a[4]')))
    login_button.click()
    time.sleep(2)

    # 输入账号
    username_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'username')))
    username_input.send_keys(account)

    # 输入密码
    password_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'password')))
    password_input.send_keys(password)

    # 点击登录
    login_submit = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'loginsubmit')))
    login_submit.click()
    time.sleep(3)

    # 访问积分规则页面
    logging.info("访问积分规则页面")
    driver.get('https://bbs.kafan.cn/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog')

    # 等待积分表格加载
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//table[@summary="积分获得历史"]')))
    logging.info("积分获得历史表格已加载")

    # 获取积分值
    credit_value = driver.find_element(By.XPATH, '//table[@summary="积分获得历史"]//tbody/tr/td[2]').text
    logging.info(f"积分值为: {credit_value}")

    # 获取最后一次签到时间
    last_signin_time = driver.find_element(By.XPATH, '//table[@summary="积分获得历史"]//tbody/tr/td[last()]').text
    logging.info(f"最后一次签到时间: {last_signin_time}")

    logging.info("回到主页")
    driver.get('https://bbs.kafan.cn/')
    time.sleep(3)

    # 获取前五个帖子
    post_elements = driver.find_elements(By.XPATH, '//*[@id="comeing_toplist"]/li/a')[:5]  # 这里使用正确的 XPATH 定位到前五个帖子
    post_titles = []
    post_links = []

    # 获取帖子标题和链接
    for post in post_elements:
        post_titles.append(post.get_attribute('title'))
        post_links.append(post.get_attribute('href'))

    # 逐个访问帖子并模拟阅读
    for i, (post_title, post_link) in enumerate(zip(post_titles, post_links)):
        logging.info(f"访问帖子 {i + 1}: {post_title}")
        driver.get(post_link)

        # 模拟阅读 5 秒钟，期间下滑页面
        for scroll in range(5):
            driver.execute_script("window.scrollBy(0, 300);")  # 每次滚动300像素
            time.sleep(1)  # 每次滚动后等待1秒

        logging.info(f"完成帖子 {i + 1} 的阅读")
        time.sleep(2)

    # 发送签到结果和帖子信息
    message = f"签到成功，目前积分为 {credit_value}，最后一次签到时间 {last_signin_time}。\n成功阅读的帖子:\n" + "\n".join(post_titles)
    send("卡饭论坛签到", message)

except TimeoutException:
    logging.error("页面元素定位失败或超时")
    send("卡饭论坛签到失败", "页面元素定位失败或超时")
except NoSuchElementException as e:
    logging.error(f"元素定位失败: {str(e)}")
    send("卡饭论坛签到失败", f"元素定位失败: {str(e)}")
finally:
    if driver:
        driver.quit()
    logging.info("浏览器已关闭")
