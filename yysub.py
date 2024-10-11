# 青龙签到脚本，cookie请填写到环境变量“yysub_cookie”
#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("人人字幕组")

import os
import requests
import time

# 请求用户信息的URL
url = "https://www.yysub.net/user/login/getCurUserTopInfo"

# 获取环境变量中的 cookie
def get_cookie():
    return os.getenv('yysub_cookie', '')

# 发起GET请求获取用户数据
def get_user_info(retry_count=3):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'cookie': get_cookie(),
    }

    while retry_count > 0:
        try:
            response = requests.get(url, headers=headers)

            # 如果请求成功，解析响应
            if response.status_code == 200:
                data = response.json()
                # 提取需要的信息
                nickname = data['data']['userinfo']['nickname']
                cont_login = data['data']['usercount']['cont_login']
                print(f"用户 {nickname} 已连续登陆 {cont_login} 天")
                break
            else:
                print(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"发生错误: {str(e)}")

        retry_count -= 1
        if retry_count > 0:
            print(f"重试中... 剩余重试次数: {retry_count}")
            time.sleep(2)  # 等待2秒后重试
        else:
            print("请求失败，已达到最大重试次数。")

# 执行签到操作
if __name__ == "__main__":
    get_user_info()
