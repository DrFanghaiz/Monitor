# 公网发布向导计划

## 目标

把 Cloudflare Tunnel 的固定域名配置流程放进软件里，用户只需要填写子域名，授权登录后由软件完成创建隧道、绑定 DNS、写入配置和启动隧道。

## 步骤

1. 检查现有 TunnelService、Settings 页面和 AppSettings 保存方式。
2. 给 TunnelService 增加 Cloudflare 固定域名配置能力。
3. 在设置页增加“公网发布向导”。
4. 构建验证，确认不影响原有临时隧道和设置页。

