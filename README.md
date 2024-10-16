# Autosign
自用青龙签到库，代码使用Chatgpt编写，不定时存在bug。


| **任务** | **来源** | **说明** | **备注** |
| --- | --- | --- | --- |
| 科研通签到 | [chenlunTian/ablesciSign](https://github.com/chenlunTian/ablesciSign) | 签到获取积分，用于悬赏论文或书籍 | 环境变量填写'ABLESCICOOKIE' |
| 夸克签到 | [BNDou/Auto\_Check\_In](https://github.com/BNDou/Auto_Check_In) | 获取夸克网盘容量 | 抓包流程：    【手机端】    ①打开抓包，手机端访问签到页    ②找到url为 https://drive-m.quark.cn/1/clouddrive/capacity/growth/info 的请求信息    ③复制url后面的参数: kps sign vcode 粘贴到环境变量    环境变量名为 COOKIE_QUARK 多账户用 回车 或 && 分开    user字段是用户名 (可是随意填写，多账户方便区分)    例如: user=张三; kps=abcdefg; sign=hijklmn; vcode=111111111; |
| follow签到 | 修改自[chavyleung/scripts](https://github.com/chavyleung/scripts) | 签到获取铸币,用于打赏或邀请 | 电脑抓包获取 csrf token 和 cookie |
| wps签到 | [wf021325/qx](https://github.com/wf021325/qx) | pc端签到领取兑换vip时间 | 抓cookie(手机用qx，loon，surge等可以自动抓cookie，请自行配置)用手机或者电脑进入https://vip.wps.cn/home登录后，找到cookie里面的wps_sid，格式如下# 青龙环境变量     wps_pc_val = {"cookie":"wps_sid=xxxxxxxxxxxx"} |
| 京东价保 | [6dylan6/jdpro](https://github.com/6dylan6/jdpro) | 京东价保 |  |
| 京东带图评价 | [6dylan6/jdpro](https://github.com/6dylan6/jdpro) | 京东评价自动化 |  |
| [雨晨ios资源网站](https://yuchen.tonghuaios.com/) | [superHao2000/autoCheck](https://github.com/superHao2000/autoCheck) | 签到获取积分，兑换ios应用下载
| 人人影视字幕组 | 自写 | 签到增加天数，无任何作用
| 花夏数娱 | 修改自[MCdasheng/QuantumultX](https://github.com/MCdasheng/QuantumultX) | 签到获取积分，兑换ios应用下载 |
| 好时充 | 自写 | 签到获取积分，据说能够抵扣现金
