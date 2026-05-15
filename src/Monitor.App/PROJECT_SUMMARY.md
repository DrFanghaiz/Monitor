# Monitor.App — .NET 8 项目总结

## 项目概述

公用机管理系统桌面应用，用 .NET 8 WPF + Blazor Hybrid 完整重写原 Python 版。  
SQLite 本地数据库，单机运行，无云端依赖。

## 技术栈

- .NET 8 + WPF + Blazor Server (BlazorWebView)
- Dapper + Microsoft.Data.Sqlite
- Serilog
- BCrypt.Net-Next
- ECharts (JS Interop)

## 如何运行

```bash
cd src/Monitor.App
dotnet run
```

运行前需确保 `bin/Debug/net8.0-windows/` 下有：
- `config.json`（已从项目根复制）
- `monitor.db`（已从项目根复制）
- `wwwroot/`（构建时自动复制）

## 项目结构

```
src/Monitor.App/
├── Program.cs / App.xaml(.cs)       ← WPF 应用入口，初始化 DB/配置/DI/服务
├── MainWindow.xaml(.cs)            ← 无边框窗口 + BlazorWebView + 自定义标题栏
├── GlobalUsings.cs                 ← global using System.IO
├── _Imports.razor                  ← Blazor 全局 using
├── Monitor.App.csproj              ← net8.0-windows, Sdk.Razor, UseWPF
│
├── Models/                         ← 数据模型 (POCO)
│   ├── UsageRecord.cs              ← 包含 UseHistoryItem, UserStat, HourlyStat, DailyStat
│   ├── Reservation.cs
│   ├── RemoteSession.cs
│   ├── AuditLog.cs
│   └── AppStatus.cs               ← 包含 LocalUseInfo, RemoteControlInfo, TimerState, SidebarStatus
│
├── Repositories/                   ← Dapper 数据访问
│   ├── IUsageRepository.cs + UsageRepository.cs
│   ├── IReservationRepository.cs + ReservationRepository.cs
│   ├── IRemoteSessionRepository.cs + RemoteSessionRepository.cs
│   └── IAuditRepository.cs + AuditRepository.cs
│
├── Services/                       ← 业务逻辑
│   ├── TimerService.cs             ← 计时核心：start/stop/state，内存状态
│   ├── ReservationService.cs       ← 预约 CRUD + 时间段冲突检测
│   ├── StatisticsService.cs        ← 统计查询（委托给 UsageRepository）
│   ├── StatusService.cs            ← 统一状态聚合（timer + remote + records + reservations）
│   ├── RemoteMonitorService.cs     ← 轮询检测远程控制软件（AnyDesk 等）
│   ├── TunnelService.cs            ← cloudflared/ngrok 子进程管理
│   ├── BackupService.cs            ← ZIP 备份数据库+配置文件
│   └── WebAccessService.cs         ← Token 认证（ConcurrentDictionary）
│
├── Infrastructure/
│   ├── Database/
│   │   ├── DbConnectionFactory.cs  ← SqliteConnection 工厂
│   │   └── SchemaInitializer.cs    ← CREATE TABLE IF NOT EXISTS（4 张表）
│   ├── Config/
│   │   └── AppSettings.cs          ← 强类型配置，JSON 读写，兼容原 config.json
│   ├── Security/
│   │   └── PasswordManager.cs      ← BCrypt 密码哈希/验证（静态方法）
│   └── System/
│       ├── InstanceLock.cs         ← Mutex 单实例锁
│       └── ProcessDetector.cs      ← 远程工具进程检测
│
├── Api/                            ← Minimal API 端点（外部 Web 访问用）
│   ├── AuthEndpoints.cs            ← POST /api/auth
│   ├── StatusEndpoints.cs          ← GET /api/status
│   ├── TimerEndpoints.cs           ← /api/timer/start|stop|state|history
│   ├── StatisticsEndpoints.cs      ← /api/statistics/users|hourly|daily|distribution
│   ├── ReservationEndpoints.cs     ← /api/reservations
│   └── SettingsEndpoints.cs        ← /api/settings
│
├── Components/                     ← Blazor UI
│   ├── App.razor                   ← 路由
│   ├── Layout/
│   │   ├── AppShell.razor          ← 侧边栏 + 主内容区布局
│   │   └── Sidebar.razor           ← 导航 + 系统状态（3 秒轮询刷新）
│   └── Pages/
│       ├── Dashboard.razor         ← / 仪表盘：状态卡片 + 快捷计时 + 今日记录/预约
│       ├── Timer.razor             ← /timer 计时页：大数字计时器
│       ├── History.razor           ← /history 历史记录：筛选 + 批量删除
│       ├── Statistics.razor        ← /statistics 统计：ECharts 饼图 + 折线图
│       ├── ReservationPage.razor   ← /reservation 预约：新建 + 列表管理
│       └── Settings.razor          ← /settings 设置：密码 + 备份 + 系统信息
│
└── wwwroot/
    ├── index.html                  ← Blazor 宿主页
    ├── css/
    │   └── app.css                 ← 全部样式：design tokens, 卡片, 按钮, 表格, 动画
    └── js/
        ├── app.js                  ← ECharts JS Interop
        └── echarts.min.js          ← ECharts 5.5 库
```

## 数据库（SQLite，4 张表）

直接读写原 Python 项目的 `monitor.db`，零迁移成本。

- **usage_records** — 使用记录（id, user_name, start_time, end_time, duration_seconds, created_at）
- **reservations** — 预约（id, user_name, date, start_hour, end_hour, status, created_at）
- **remote_sessions** — 远程会话（id, remote_type, start_time, end_time, duration_seconds, is_active, created_at）
- **audit_log** — 审计日志（id, action, details, timestamp）

## 配置文件（config.json）

20+ 个键，与 Python 版格式完全兼容。关键键：
- admin_password_hash, default_password, web_server_password
- web_server_port (8080), web_server_enabled
- tunnel_enabled, tunnel_mode ("cloudflared"|"ngrok"), tunnel_cloudflared_path, tunnel_ngrok_path
- remote_monitor_enabled, remote_monitor_interval, remote_tools (进程名列表)
- auto_backup, backup_retention_days, backup_path
- theme, language, window_always_on_top, minimize_to_tray

## UI 样式要点

**设计风格：** 深色控制台风，青蓝色强调色。

**CSS 变量（app.css 开头）：**
- `--bg-primary: #0f0f13` 页面背景
- `--bg-secondary: #16161d` 侧边栏背景
- `--bg-card: #1a1a24` 卡片背景
- `--accent: #5b9bd5` 主色调
- `--success: #4ecdc4` / `--danger: #e0556a` / `--warning: #f0a060`

**UI 组件复用类：** `.card`, `.btn`, `.btn-primary`, `.btn-danger`, `.btn-ghost`, `.input`, `.badge`, `.badge-success`, `.badge-warning`, `.badge-danger`, `.status-dot`, `.status-dot.idle`, `.status-dot.in_use`, `.status-dot.remote_controlled`, `.sidebar`, `.sidebar-item`, `.sidebar-item.active`, `.table-row`, `.table-header`, `.kpi-value`, `.kpi-label`, `.timer-display`, `.chart-box`

**窗口：** 无边框 WPF 窗口（WindowStyle=None），12px 圆角，暗色背景，40px 高自定义标题栏。

## Blazor 组件通信方式

- **Blazor → Service → Repository → SQLite**（直接 DI 注入，不走 HTTP）
- 侧边栏状态：`System.Threading.Timer` 每 3 秒刷新
- 仪表盘：每 5 秒刷新
- 计时页：每 200ms 刷新（高频更新计时器数字）
- ECharts 图表：通过 `IJSRuntime.InvokeVoidAsync("renderChart", ...)` 调用 JS

## 待完善项

1. **系统托盘** — 当前未实现（原 Python 用 pystray）
2. **窗口拖动** — 自定义标题栏的拖动逻辑已写但需测试
3. **远程监控** — ProcessDetector 已实现但需在 Windows 上实际测试
4. **Tunnel** — 需要 cloudflared.exe 或 ngrok.exe 在 PATH 中
5. **ECharts** — 图表页面已写但需验证渲染效果
6. **响应式** — 当前以 1200x800 为基准设计
7. **错误边界** — Blazor ErrorBoundary 未添加
8. **API 层注册** — Minimal API 端点已定义但未在 App.xaml.cs 中注册启动（当前 Blazor 直接注入 Service，API 仅预留）

## 与 Python 原项目的关键行为差异（无）

行为完全一致：
- 计时器状态在内存中，重启后丢失（与 Python 同）
- 预约冲突检测逻辑相同（时间段重叠 SQL）
- 远程检测进程轮询间隔相同（可配置）
- 配置文件热保存（每次修改立即写入磁盘）
- 数据库时间格式完全相同（TEXT 列，"yyyy-MM-dd HH:mm:ss"）
