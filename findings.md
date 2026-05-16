# 公网发布向导发现

## 现状

- 当前 TunnelService 只会启动临时 `trycloudflare.com` 隧道。
- 固定域名需要用户手动执行 `login/create/route dns/config/run`，对普通用户太复杂。
- Cloudflare 登录授权不能完全自动化，必须打开浏览器让用户确认一次。

## 设计结论

- 软件可以自动处理创建隧道、绑定域名、生成 `config.yml` 和启动隧道。
- 用户仍需要先把域名接入 Cloudflare，并完成一次浏览器授权。
- 安装系统服务需要管理员权限，本阶段先不强行自动安装服务，避免引入权限问题。

