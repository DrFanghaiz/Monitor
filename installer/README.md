# Monitor 安装包构建

运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build-installer.ps1
```

脚本会完成三件事：

1. 发布 `win-x64` 自包含版本。
2. 把 `cloudflared.exe` 放入发布目录。
3. 调用 Inno Setup 生成 `artifacts\installer\Monitor-Setup.exe`。

前提：

- 已安装 `.NET 8 SDK`
- 已安装 `Inno Setup 6`
- 仓库根目录存在 `cloudflared.exe`

安装包行为：

- 主程序安装到 `C:\Program Files\Monitor\`
- 数据目录使用 `C:\ProgramData\Monitor\`
- 创建开始菜单快捷方式
- 可选桌面快捷方式
- 可选开机自启
- 安装前检查 `WebView2 Runtime`
