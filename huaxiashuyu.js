#!/usr/bin/env bash
// cron:0 8 * * *
// new Env("花夏数娱签到脚本")

const axios = require('axios');
const qs = require('qs');
const { exec } = require('child_process');  // 用来执行 Python 脚本

// 从环境变量中获取账号和密码
const username = process.env.HXSY_USERNAME;  // 账号
const password = process.env.HXSY_PASSWORD;  // 密码

if (!username || !password) {
  notify("花夏数娱签到脚本", "未设置账号或密码，请在环境变量中设置HXSY_USERNAME和HXSY_PASSWORD");
  return;
}

// 生成登录body
const loginBody = qs.stringify({
  action: 'user_login',
  username: username,
  password: password
});

(async () => {
  try {
    const cookie = await login();
    if (cookie) {
      await signIn(cookie);
    }
  } catch (error) {
    notify("花夏数娱签到脚本", `脚本执行出错：${error.message}`);
  }
})();

async function login() {
  const options = {
    method: 'POST',
    url: 'https://www.huaxiashuyu.com/wp-admin/admin-ajax.php',
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    data: loginBody
  };

  try {
    const response = await axios(options);
    const setCookie = response.headers['set-cookie'];
    if (response.data.status == 1) {
      notify("花夏数娱签到脚本", `🎉 登录成功: ${response.data.msg}`);
      const cookie = parseCookie(setCookie);
      return cookie;
    } else {
      notify("花夏数娱签到脚本", `🔴 登录失败: ${response.data.msg}`);
      return null;
    }
  } catch (error) {
    notify("花夏数娱签到脚本", `❌ 登录错误：${error.message}`);
    return null;
  }
}

async function signIn(cookie) {
  const options = {
    method: 'POST',
    url: 'https://www.huaxiashuyu.com/wp-admin/admin-ajax.php',
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Cookie': cookie
    },
    data: qs.stringify({ action: 'user_qiandao' })
  };

  try {
    const response = await axios(options);
    notify("花夏数娱签到脚本", "🟢 正在签到...");
    if (response.data.status == 1) {
      notify("花夏数娱签到脚本", `🎉 签到成功: ${response.data.msg}`);
    } else {
      notify("花夏数娱签到脚本", `🔴 签到失败: ${response.data.msg}`);
    }
  } catch (error) {
    notify("花夏数娱签到脚本", `❌ 签到错误：${error.message}`);
  }
}

function parseCookie(setCookie) {
  let cookie = '';
  setCookie.forEach(item => {
    cookie += item.split(';')[0] + '; ';
  });
  return cookie.trim();
}

// 调用 Python notify.py 中的 send 函数进行通知
function notify(title, content) {
  const command = `python3 /path/to/notify.py "${title}" "${content}"`;
  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`通知失败: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`通知错误: ${stderr}`);
      return;
    }
    console.log(`通知结果: ${stdout}`);
  });
}
