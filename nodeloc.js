
#!/usr/bin/env bash
// cron:0 */6 * * *
// new Env("Nodeloc永久装扮监控")

/*
功能：监控Nodeloc网站是否有新的未购买的永久装扮上架
环境变量：nodeloc - 存储登录cookie

========= 环境变量说明 =========
支持以下几种cookie格式：

1. 简单格式（直接粘贴cookie）:
nodeloc = "flarum_lscache_vary=xxxx; flarum_session=yyyy"

2. 复杂格式（从浏览器开发者工具直接复制）:
nodeloc = "Set-Cookie: flarum_lscache_vary=xxxx; Path=/; Expires=Sun, 30 Mar 2025 10:40:57 GMT
Set-Cookie: flarum_session=yyyy; Path=/; Expires=Sun, 30 Mar 2025 10:40:57 GMT"

3. 完整请求头（包含其他cookie）:
nodeloc = "cookie: _ga=GA1.2.xxxxx; flarum_lscache_vary=xxxx; flarum_session=yyyy"

脚本会自动提取所需的flarum_lscache_vary和flarum_session值
*/


const axios = require('axios');
const $ = new Env('Nodeloc永久装扮监控');
const notify = $.isNode() ? require('./sendNotify') : '';

// 装扮类型中文映射
const itemTypeMap = {
  'profileBackground': '用户卡背景图片',
  'avatarFrame': '头像边框',
  'usernameColor': '用户名颜色'
};

// 从复杂格式中提取cookie值
function extractCookies(cookieStr) {
  const cookies = {};
  
  // 处理可能的多行文本
  const lines = cookieStr.split('\n');
  
  lines.forEach(line => {
    // 移除可能的"Set-Cookie:"前缀
    let processedLine = line.replace(/^Set-Cookie:\s*/i, '');
    
    // 分割cookie片段
    const segments = processedLine.split(/;\s*/);
    
    segments.forEach(segment => {
      // 查找形如key=value的部分
      const match = segment.match(/^([^=]+)=(.*)$/);
      if (match) {
        const [, key, value] = match;
        cookies[key.trim()] = value.trim();
      }
    });
  });
  
  return cookies;
}

// 构建有效的cookie字符串
function buildCookieString(cookieObj) {
  const requiredFields = ['flarum_lscache_vary', 'flarum_session'];
  const validCookies = [];
  
  for (const field of requiredFields) {
    if (cookieObj[field]) {
      validCookies.push(`${field}=${cookieObj[field]}`);
    }
  }
  
  return validCookies.join('; ');
}

!(async () => {
  try {
    // 从环境变量中读取cookie
    const rawCookie = process.env.nodeloc;
    if (!rawCookie) {
      console.log('未设置nodeloc环境变量，请先设置cookie');
      // 当未设置cookie时也发送通知
      if (notify) {
        await notify.sendNotify('Nodeloc永久装扮监控异常', '未设置nodeloc环境变量，请先配置cookie');
      }
      return;
    }
    
    // 解析cookie，无论是简单格式还是复杂格式
    const cookieObj = extractCookies(rawCookie);
    const cookie = buildCookieString(cookieObj);
    
    // 检查cookie是否包含必要的部分
    if (!cookie.includes('flarum_lscache_vary') || !cookie.includes('flarum_session')) {
      console.log('无法从环境变量中提取有效的cookie，应包含flarum_lscache_vary和flarum_session');
      await notify.sendNotify('Nodeloc永久装扮监控异常', '无法从环境变量中提取有效的cookie，请检查环境变量设置');
      return;
    }

    console.log('开始检查Nodeloc装扮商店...');
    const response = await axios.get('https://www.nodeloc.com/api/decorationStoreList', {
      params: {
        'filter[item_type]': -1,
        'filter[purchase_type]': -1,
        'filter[isActivate]': 1
      },
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cookie': cookie
      }
    });

    const items = response.data.data;
    let newItems = [];

    for (const item of items) {
      const attributes = item.attributes;
      // 检查是否是永久物品且用户未购买
      if (attributes.purchase_type === 'onetime' && attributes.purchase_id === null) {
        const typeChinese = itemTypeMap[attributes.item_type] || attributes.item_type;
        const stock = 100 - attributes.item_sold;
        
        newItems.push({
          title: attributes.item_title,
          type: typeChinese,
          cost: attributes.item_cost,
          stock: stock
        });
      }
    }

    // 只在发现新物品时发送通知
    if (newItems.length > 0) {
      let message = 'Nodeloc有新的永久装扮上架，请及时购买！\n\n';
      
      for (const item of newItems) {
        message += `${item.type}装扮 ${item.title}，售价为${item.cost}能量，库存为${item.stock}\n`;
      }
      
      console.log(message);
      if (notify) {
        await notify.sendNotify('Nodeloc永久装扮上新', message);
      }
    } else {
      console.log('没有发现新的永久装扮');
      // 没有发现新物品时不发送通知
    }
  } catch (error) {
    console.log('请求出错：' + error.message);
    // 脚本出错时发送通知
    if (notify) {
      await notify.sendNotify('Nodeloc永久装扮监控异常', `脚本运行出错：${error.message}`);
    }
  }
})();

// 工具函数
function Env(t,e){class s{constructor(t){this.env=t}send(t,e="GET"){t="string"==typeof t?{url:t}:t;let s=this.get;return"POST"===e&&(s=this.post),new Promise((e,i)=>{s.call(this,t,(t,s,r)=>{t?i(t):e(s)})})}get(t){return this.send.call(this.env,t)}post(t){return this.send.call(this.env,t,"POST")}}return new class{constructor(t,e){this.name=t,this.http=new s(this),this.data=null,this.dataFile="box.dat",this.logs=[],this.isMute=!1,this.isNeedRewrite=!1,this.logSeparator="\n",this.encoding="utf-8",this.startTime=(new Date).getTime(),Object.assign(this,e),this.log("",`🔔${this.name}, 开始!`)}isNode(){return"undefined"!=typeof module&&!!module.exports}isQuanX(){return"undefined"!=typeof $task}isSurge(){return"undefined"!=typeof $httpClient&&"undefined"==typeof $loon}isLoon(){return"undefined"!=typeof $loon}isShadowrocket(){return"undefined"!=typeof $rocket}toObj(t,e=null){try{return JSON.parse(t)}catch{return e}}toStr(t,e=null){try{return JSON.stringify(t)}catch{return e}}getjson(t,e){let s=e;const i=this.getdata(t);if(i)try{s=JSON.parse(this.getdata(t))}catch{}return s}setjson(t,e){try{return this.setdata(JSON.stringify(t),e)}catch{return!1}}getScript(t){return new Promise(e=>{this.get({url:t},(t,s,i)=>e(i))})}runScript(t,e){return new Promise(s=>{let i=this.getdata("@chavy_boxjs_userCfgs.httpapi");i=i?i.replace(/\n/g,"").trim():i;let r=this.getdata("@chavy_boxjs_userCfgs.httpapi_timeout");r=r?1*r:20,r=e&&e.timeout?e.timeout:r;const[o,h]=i.split("@"),a={url:`http://${h}/v1/scripting/evaluate`,body:{script_text:t,mock_type:"cron",timeout:r},headers:{"X-Key":o,Accept:"*/*"}};this.post(a,(t,e,i)=>s(i))}).catch(t=>this.logErr(t))}loaddata(){if(!this.isNode())return{};{this.fs=this.fs?this.fs:require("fs"),this.path=this.path?this.path:require("path");const t=this.path.resolve(this.dataFile),e=this.path.resolve(process.cwd(),this.dataFile),s=this.fs.existsSync(t),i=!s&&this.fs.existsSync(e);if(!s&&!i)return{};{const i=s?t:e;try{return JSON.parse(this.fs.readFileSync(i))}catch(t){return{}}}}}writedata(){if(this.isNode()){this.fs=this.fs?this.fs:require("fs"),this.path=this.path?this.path:require("path");const t=this.path.resolve(this.dataFile),e=this.path.resolve(process.cwd(),this.dataFile),s=this.fs.existsSync(t),i=!s&&this.fs.existsSync(e),r=JSON.stringify(this.data);s?this.fs.writeFileSync(t,r):i?this.fs.writeFileSync(e,r):this.fs.writeFileSync(t,r)}}lodash_get(t,e,s){const i=e.replace(/\[(\d+)\]/g,".$1").split(".");let r=t;for(const t of i)if(r=Object(r)[t],void 0===r)return s;return r}lodash_set(t,e,s){return Object(t)!==t?t:(Array.isArray(e)||(e=e.toString().match(/[^.[\]]+/g)||[]),e.slice(0,-1).reduce((t,s,i)=>Object(t[s])===t[s]?t[s]:t[s]=Math.abs(e[i+1])>>0==+e[i+1]?[]:{},t)[e[e.length-1]]=s,t)}getdata(t){let e=this.getval(t);if(/^@/.test(t)){const[,s,i]=/^@(.*?)\.(.*?)$/.exec(t),r=s?this.getval(s):"";if(r)try{const t=JSON.parse(r);e=t?this.lodash_get(t,i,""):e}catch(t){e=""}}return e}setdata(t,e){let s=!1;if(/^@/.test(e)){const[,i,r]=/^@(.*?)\.(.*?)$/.exec(e),o=this.getval(i),h=i?"null"===o?null:o||"{}":"{}";try{const e=JSON.parse(h);this.lodash_set(e,r,t),s=this.setval(JSON.stringify(e),i)}catch(e){const o={};this.lodash_set(o,r,t),s=this.setval(JSON.stringify(o),i)}}else s=this.setval(t,e);return s}getval(t){return this.isSurge()||this.isLoon()?$persistentStore.read(t):this.isQuanX()?$prefs.valueForKey(t):this.isNode()?(this.data=this.loaddata(),this.data[t]):this.data&&this.data[t]||null}setval(t,e){return this.isSurge()||this.isLoon()?$persistentStore.write(t,e):this.isQuanX()?$prefs.setValueForKey(t,e):this.isNode()?(this.data=this.loaddata(),this.data[e]=t,this.writedata(),!0):this.data&&this.data[e]||null}initGotEnv(t){this.got=this.got?this.got:require("got"),this.cktough=this.cktough?this.cktough:require("tough-cookie"),this.ckjar=this.ckjar?this.ckjar:new this.cktough.CookieJar,t&&(t.headers=t.headers?t.headers:{},void 0===t.headers.Cookie&&void 0===t.cookieJar&&(t.cookieJar=this.ckjar))}get(t,e=(()=>{})){if(t.headers&&(delete t.headers["Content-Type"],delete t.headers["Content-Length"]),this.isSurge()||this.isLoon())this.isSurge()&&this.isNeedRewrite&&(t.headers=t.headers||{},Object.assign(t.headers,{"X-Surge-Skip-Scripting":!1})),$httpClient.get(t,(t,s,i)=>{!t&&s&&(s.body=i,s.statusCode=s.status),e(t,s,i)});else if(this.isQuanX())this.isNeedRewrite&&(t.opts=t.opts||{},Object.assign(t.opts,{hints:!1})),$task.fetch(t).then(t=>{const{statusCode:s,statusCode:i,headers:r,body:o}=t;e(null,{status:s,statusCode:i,headers:r,body:o},o)},t=>e(t));else if(this.isNode()){let s=require("iconv-lite");this.initGotEnv(t),this.got(t).on("redirect",(t,e)=>{try{if(t.headers["set-cookie"]){const s=t.headers["set-cookie"].map(this.cktough.Cookie.parse).toString();s&&this.ckjar.setCookieSync(s,null),e.cookieJar=this.ckjar}}catch(t){this.logErr(t)}}).then(t=>{const{statusCode:i,statusCode:r,headers:o,rawBody:h}=t;e(null,{status:i,statusCode:r,headers:o,rawBody:h},s.decode(h,this.encoding))},t=>{const{message:i,response:r}=t;e(i,r,r&&s.decode(r.rawBody,this.encoding))})}}post(t,e=(()=>{})){const s=t.method?t.method.toLocaleLowerCase():"post";if(t.body&&t.headers&&!t.headers["Content-Type"]&&(t.headers["Content-Type"]="application/x-www-form-urlencoded"),t.headers&&delete t.headers["Content-Length"],this.isSurge()||this.isLoon())this.isSurge()&&this.isNeedRewrite&&(t.headers=t.headers||{},Object.assign(t.headers,{"X-Surge-Skip-Scripting":!1})),$httpClient[s](t,(t,s,i)=>{!t&&s&&(s.body=i,s.statusCode=s.status),e(t,s,i)});else if(this.isQuanX())t.method=s,this.isNeedRewrite&&(t.opts=t.opts||{},Object.assign(t.opts,{hints:!1})),$task.fetch(t).then(t=>{const{statusCode:s,statusCode:i,headers:r,body:o}=t;e(null,{status:s,statusCode:i,headers:r,body:o},o)},t=>e(t));else if(this.isNode()){let i=require("iconv-lite");this.initGotEnv(t);const{url:r,...o}=t;this.got[s](r,o).then(t=>{const{statusCode:s,statusCode:r,headers:o,rawBody:h}=t;e(null,{status:s,statusCode:r,headers:o,rawBody:h},i.decode(h,this.encoding))},t=>{const{message:s,response:r}=t;e(s,r,r&&i.decode(r.rawBody,this.encoding))})}}time(t,e=null){const s=e?new Date(e):new Date;let i={"M+":s.getMonth()+1,"d+":s.getDate(),"H+":s.getHours(),"m+":s.getMinutes(),"s+":s.getSeconds(),"q+":Math.floor((s.getMonth()+3)/3),S:s.getMilliseconds()};/(y+)/.test(t)&&(t=t.replace(RegExp.$1,(s.getFullYear()+"").substr(4-RegExp.$1.length)));for(let e in i)new RegExp("("+e+")").test(t)&&(t=t.replace(RegExp.$1,1==RegExp.$1.length?i[e]:("00"+i[e]).substr((""+i[e]).length)));return t}msg(e=t,s="",i="",r){const o=t=>{if(!t)return t;if("string"==typeof t)return this.isLoon()?t:this.isQuanX()?{"open-url":t}:this.isSurge()?{url:t}:void 0;if("object"==typeof t){if(this.isLoon()){let e=t.openUrl||t.url||t["open-url"],s=t.mediaUrl||t["media-url"];return{openUrl:e,mediaUrl:s}}if(this.isQuanX()){let e=t["open-url"]||t.url||t.openUrl,s=t["media-url"]||t.mediaUrl,i=t["update-pasteboard"]||t.updatePasteboard;return{"open-url":e,"media-url":s,"update-pasteboard":i}}if(this.isSurge()){let e=t.url||t.openUrl||t["open-url"];return{url:e}}}};if(this.isMute||(this.isSurge()||this.isLoon()?$notification.post(e,s,i,o(r)):this.isQuanX()&&$notify(e,s,i,o(r))),!this.isMuteLog){let t=["","==============📣系统通知📣=============="];t.push(e),s&&t.push(s),i&&t.push(i),console.log(t.join("\n")),this.logs=this.logs.concat(t)}}log(...t){t.length>0&&(this.logs=[...this.logs,...t]),console.log(t.join(this.logSeparator))}logErr(t,e){const s=!this.isSurge()&&!this.isQuanX()&&!this.isLoon();s?this.log("",`❗️${this.name}, 错误!`,t.stack):this.log("",`❗️${this.name}, 错误!`,t)}wait(t){return new Promise(e=>setTimeout(e,t))}done(t={}){const e=(new Date).getTime(),s=(e-this.startTime)/1e3;this.log("",`🔔${this.name}, 结束! 🕛 ${s} 秒`),this.log(),(this.isSurge()||this.isQuanX()||this.isLoon())&&$done(t)}}(t,e)}
