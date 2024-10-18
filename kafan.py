from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from notify import send  # 从 notify.py 中导入发送通知的功能

# 读取青龙面板中的账号和密码
ql_env = os.getenv("kafan_ACCOUNT_PASSWORD")
if ql_env:
    account, password = ql_env.split("&")
else:
    send("未找到青龙面板中的账号和密码环境变量")  # 发送错误通知
    raise Exception("未找到青龙面板中的账号和密码环境变量")

# 初始化Selenium WebDriver
driver = webdriver.Chrome()

try:
    # 1. 访问卡饭论坛
    driver.get('https://bbs.kafan.cn/')
    time.sleep(2)  # 等待页面加载

    # 2. 点击“快速登陆”
    login_button = driver.find_element(By.XPATH, '//*[@id="comeing_toptb"]/div/div[2]/a[4]')
    login_button.click()
    time.sleep(2)

    # 3. 输入账号
    username_input = driver.find_element(By.XPATH, '//*[@id="username_Lxhht"]')
    username_input.send_keys(account)

    # 4. 输入密码
    password_input = driver.find_element(By.XPATH, '//*[@id="password3_Lxhht"]')
    password_input.send_keys(password)

    # 5. 点击登录
    login_submit = driver.find_element(By.XPATH, '//*[@id="loginform_Lxhht"]/div/div[6]/table/tbody/tr/td[1]/button/strong')
    login_submit.click()
    time.sleep(3)  # 等待页面跳转

    # 6. 点击签到
    signin_button = driver.find_element(By.XPATH, '//img[@class="qq_bind" and @src="https://a.kafan.cn/plugin/dsu_amupper/images/wb.png"]')
    signin_button.click()
    time.sleep(2)

    # 7. 访问积分规则页面，获取签到信息
    driver.get('https://bbs.kafan.cn/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog')
    time.sleep(2)

    # 8. 获取签到天数和最后一次签到时间
    login_days = driver.find_element(By.XPATH, '//*[@id="ct"]/div[1]/div/table/tbody/tr[2]/td[2]').text
    last_signin_time = driver.find_element(By.XPATH, '//*[@id="ct"]/div[1]/div/table/tbody/tr[2]/td[11]').text

    # 9. 获取帖子标题（先获取标题，再点击）
    post_title = driver.find_element(By.XPATH, '//a[contains(@href, "thread-2274940")]').get_attribute('title')

    # 10. 点击帖子
    post_link = driver.find_element(By.XPATH, '//a[contains(@href, "thread-2274940")]')
    post_link.click()

    # 等待页面加载
    time.sleep(3)

    # 11. 输出签到信息，包含帖子阅读信息
    message = f'签到成功，目前签到 {login_days} 天，最后一次签到时间 {last_signin_time}，成功阅读帖子 "{post_title}"'
    print(message)

    # 发送签到结果通知
    send(message)

except Exception as e:
    # 捕获并发送错误通知
    error_message = f"签到过程出错，错误信息：{str(e)}"
    send(error_message)
    print(error_message)

finally:
    # 关闭浏览器
    driver.quit()
