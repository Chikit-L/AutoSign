#!/usr/bin/env bash
// cron:0 8 * * *
// new Env("花夏数娱签到脚本")

const axios = require('axios');
const qs = require('qs');
const { execSync } = require('child_process');

// 检查依赖是否已安装，如果没有则安装依赖
function checkAndInstallDependencies() {
  try {
    require.resolve('axios');
    require.resolve('qs');
  } catch (e) {
    console.log("检测到缺失依赖，正在安装依赖...");
    try {
      execSync('npm install axios qs', { stdio: 'inherit' });
      console.log("依赖安装完成。");
    } catch (error) {
      console.error("❌ 依赖安装失败：", error);
      process.exit(1);
    }
  }
}

// 执行依赖检测和安装
checkAndInstallDependencies();

// 从环境变量中获取账号和密码
const username = process.env.HXSY_USERNAME;  // 账号
const password = process.env.HXSY_PASSWORD;  // 密码

if (!username || !password) {
  console.log("未设置账号或密码，请在环境变量中设置HXSY_USERNAME和HXSY_PASSWORD");
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
    console.error("脚本执行出错：", error);
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
      console.log("🎉 登录成功: " + response.data.msg);
      const cookie = parseCookie(setCookie);
      return cookie;
    } else {
      console.log("🔴 登录失败: " + response.data.msg);
      return null;
    }
  } catch (error) {
    console.error("❌ 登录错误：", error);
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
    console.log("🟢 正在签到...");
    if (response.data.status == 1) {
      console.log("🎉 签到成功: " + response.data.msg);
    } else {
      console.log("🔴 签到失败: " + response.data.msg);
    }
  } catch (error) {
    console.error("❌ 签到错误：", error);
  }
}

function parseCookie(setCookie) {
  let cookie = '';
  setCookie.forEach(item => {
    cookie += item.split(';')[0] + '; ';
  });
  return cookie.trim();
}
