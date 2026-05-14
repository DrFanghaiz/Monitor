# Monitor 远程占用监控发现记录

## 产品发现

- 用户修正了产品核心：Monitor 的主目标不是公用机计时，而是监控同一台机器是否正在被远程控制软件占用。
- 关键远程控制软件包括向日葵、ToDesk、AnyDesk，后续可以扩展到 RDP、RustDesk 等。
- 远程状态需要发布到一个网址，供其他人连接前查看，避免控制冲突。
- "操作人"是核心字段。仅检测到远程进程不够，必须能知道或记录是谁在使用。

## 设计发现

- 首页应该优先回答"现在能不能连这台机器"，而不是展示普通计时数据。
- Web 发布页比本机端更接近用户决策入口，必须极简、清楚、可刷新。
- 手动计时、预约、统计是辅助能力，不能抢主功能层级。

## 风险发现

- 很多远程控制软件存在后台常驻进程。仅凭进程存在判断"正在使用"可能误报。
- 操作人无法完全自动识别，必须设计登记、认领或管理员确认流程。
- 如果状态检测失败，不能显示"空闲"，应显示"状态未知"或"需要确认"。

---

# 阶段 1 审计报告（2026-05-14）

## 审计结论

当前代码具备远程检测和 Web 发布的基本骨架，但存在三个严重问题：

1. **状态模型不完整**：`StatusService` 只区分 `idle` / `in_use` / `remote_controlled`，缺少"未知"和"异常"。如果检测服务挂了，当前会直接显示"空闲"，这是最高风险项。
2. **远程会话缺少操作人**：`remote_sessions` 表只有 remote_type 和起止时间，没有任何记录操作人的字段。检测到远程占用后，不知道是谁在使用。
3. **UI 主次颠倒**：Dashboard 首页把手动计时放第一位，远程状态放在第四个指标卡片中。历史记录页只展示手动计时数据，没有远程会话历史入口。统计页也围绕手动计时。

## 现有能力

### 远程检测能力

| 文件 | 已有能力 | 评注 |
|------|----------|------|
| `RemoteMonitorService.cs` | Timer 轮询检测，检测到/结束时写入 remote_sessions 表 | 只做二态切换（有/无远程），不区分检测失败 |
| `ProcessDetector.cs` | `Process.GetProcessesByName()` 匹配进程名，映射到工具名 | **只检查进程是否存在**，不区分后台服务 vs 活跃远程会话。映射表硬编码在 switch 中 |
| `AppSettings.cs` | `remote_monitor_enabled`, `remote_monitor_interval`, `remote_tools`（List\<string\>） | 配置已集中，但只是进程名列表，无检测深度配置 |
| `ProcessDetector` 支持的工具 | sunlogin, teamviewer, anydesk, todesk, mstsc, msrdc | 6 种工具，AnyDesk 同时检查 32/64 位进程名 |

### Web 发布能力

| 文件 | 已有能力 | 评注 |
|------|----------|------|
| `TunnelService.cs` | cloudflared / ngrok 子进程管理，解析公网 URL | 需要可执行文件在 PATH 中；URL 不在 UI 中展示 |
| `WebAccessService.cs` | 密码验证 → Guid token，ConcurrentDictionary 存储 | 无 token 过期，无 JWT，重启后所有 token 失效 |
| `StatusEndpoints.cs` | `GET /api/status` 返回完整状态 JSON，含 remote_control 字段 | API 已存在但**未在 App.xaml.cs 中注册启动**（当前不可用） |
| `AuthEndpoints.cs` | `POST /api/auth` 返回固定 token "desktop-session" | 可用但简陋 |

### 数据库能力

| 表（remote_sessions） | 现有字段 | 类型 |
|-----------------------|----------|------|
| id | INTEGER PK AUTOINCREMENT | ✓ |
| remote_type | TEXT NOT NULL | ✓ 工具名 |
| start_time | TEXT NOT NULL | ✓ |
| end_time | TEXT | ✓ 可为 NULL |
| duration_seconds | INTEGER DEFAULT 0 | ✓ julianday 计算 |
| is_active | INTEGER DEFAULT 1 | ✓ 布尔 |
| created_at | TEXT DEFAULT CURRENT_TIMESTAMP | ✓ |

**缺失字段：**
- `operator_name` — 操作人姓名（核心缺失）
- `source` — 检测来源（process / window / manual_claim）
- `end_reason` — 结束原因（normal / timeout / manual / error）
- `last_seen_at` — 最后一次检测到的时间
- `status` — 会话状态（active / unknown / ended）
- `confidence` — 检测置信度

### 状态模型

当前 StatusService.GetFullStatus() 的 computerStatus 有三种：
- `"idle"` — 无远程 + 无手动计时
- `"in_use"` — 无远程 + 手动计时中
- `"remote_controlled"` — 有远程

**缺失状态：**
- 检测服务不可用时的标记
- 配置关闭检测时的标记
- 检测到进程但不确定是否真正在远程控制时的标记

## 缺口

### 高优先级

| 缺口 | 影响 | 涉及文件 |
|------|------|----------|
| 状态缺少"未知" | 检测挂了会显示"空闲"，后来者会在不知情的情况下连接 | StatusService.cs, AppStatus.cs |
| 远程会话无操作人 | 知道被占用了但不知道谁在用，历史记录无法追溯 | RemoteSession.cs, RemoteSessionRepository.cs, SchemaInitializer.cs |
| API 未注册 | Web 发布功能不可用，公网 URL 无人能访问 | App.xaml.cs（需注册 MapXxxEndpoints） |
| 进程检测只查进程名 | 开机后台常驻也被判定为"使用中"，误报率很高 | ProcessDetector.cs |
| 首页主次颠倒 | 用户先看见手动计时，远程状态被藏在第四张卡片 | Dashboard.razor |

### 中优先级

| 缺口 | 影响 | 涉及文件 |
|------|------|----------|
| 历史记录只看 usage_records | 远程会话历史无法在 UI 中查看 | History.razor |
| 统计页围绕手动计时 | 图表显示的是用户使用分布，不是远程占用统计 | Statistics.razor |
| 设置页无远程检测配置 | 不能增删远程工具、不能看 Web 发布 URL、不能调检测间隔 | Settings.razor |
| 文案含糊 | Dashboard 显示"安全"，应该是"未检测到远程占用" | Dashboard.razor |
| 删除无确认 | 历史记录删除没有二次确认 | History.razor, TimerEndpoints.cs |

### 低优先级

| 缺口 | 影响 | 涉及文件 |
|------|------|----------|
| Token 无过期 | 安全风险低（本地应用，tunnel 通常有 cloudflare 防护） | WebAccessService.cs |
| Tunnel URL 不在 UI 展示 | 管理员不知道公网地址 | Settings.razor, TunnelService.cs |
| 系统托盘未实现 | 关闭窗口后进程退出 | 无托盘代码 |

## 阶段 2 建议改动（最小闭环：让远程占用监控可用）

只做最小改动，让"检测远程 → 记录会话 → 发布状态到 Web → 首页显示远程状态"这个闭环跑通。

### 2.1 新增 AppStatus 状态值

**文件：** `src/Monitor.App/Models/AppStatus.cs`

- 增加 `"unknown"`（检测不可用）和 `"error"`（检测异常）到 computerStatus 的约定值
- `RemoteControlInfo` 增加字段：`Confidence`, `Source`, `OperatorName`, `LastSeenAt`

### 2.2 修改 StatusService 状态判定逻辑

**文件：** `src/Monitor.App/Services/StatusService.cs`

- 如果 `RemoteMonitorEnabled == false`，computerStatus 设为 `"unknown"` 而非 `"idle"`
- 如果 RemoteMonitorService 在一个检测周期内未返回结果（需要加超时标记），设为 `"unknown"`
- 如果检测异常（Timer 抛异常），设为 `"error"`
- 文案：远程状态的相关显示从"安全"改为"未检测到远程占用"

### 2.3 修改 ProcessDetector，增加检测深度标记

**文件：** `src/Monitor.App/Infrastructure/System/ProcessDetector.cs`

- `Detect()` 返回结果从 `string?` 改为包含 tool name 和 detection source 的结构
- 每个工具增加配置标记（目前先硬编码一份集中映射，后续阶段迁移到配置文件）
- 保留"只检测进程存在"的逻辑，但返回时标记 `source = "process"` 和 `confidence = "low"`

### 2.4 数据库：增加 operator_name 和 source 字段

**文件：** `src/Monitor.App/Infrastructure/Database/SchemaInitializer.cs`

- `remote_sessions` 表增加列（ALTER TABLE ADD COLUMN）：
  - `operator_name TEXT DEFAULT ''`
  - `source TEXT DEFAULT 'process'`
  - `end_reason TEXT DEFAULT ''`
  - `last_seen_at TEXT DEFAULT ''`

使用 `ALTER TABLE ... ADD COLUMN` 而不是重建表，不破坏已有数据。

### 2.5 更新 RemoteSession 模型和 Repository

**文件：**
- `src/Monitor.App/Models/RemoteSession.cs` — 增加字段
- `src/Monitor.App/Repositories/RemoteSessionRepository.cs` — 查询和写入覆盖新字段
- `src/Monitor.App/Repositories/IRemoteSessionRepository.cs` — 接口同步

### 2.6 更新 RemoteMonitorService，写入操作人和来源

**文件：** `src/Monitor.App/Services/RemoteMonitorService.cs`

- `CheckAndUpdate()` 在检测到远程时写入 `source = "process"`, `operator_name = ""`（留空，后续支持登记）
- 新增 `UpdateOperatorName(int sessionId, string name)` 方法供后续操作人登记用
- 加检测失败标记（在 Timer 回调中 try-catch，异常时标记检测状态为 `unknown`）

### 2.7 注册 API 端点

**文件：** `src/Monitor.App/App.xaml.cs`

- 在 `application.Run()` 之前注册 API 端点（当前仅注册了 DI 服务，API 端点未挂载）
- 启动 Kestrel 监听 `127.0.0.1:8000`（或配置的端口）
- 注册静态文件服务（wwwroot）

### 2.8 Dashboard.razor 文案修正

**文件：** `src/Monitor.App/Components/Pages/Dashboard.razor`

- 远程状态卡片文案从"安全"改为"未检测到远程占用"
- 不做 UI 布局大改动（留到后续阶段）

### 2.9 Settings.razor 增加 Web 发布 URL 显示

**文件：** `src/Monitor.App/Components/Pages/Settings.razor`

- 在系统信息区域增加"Web 发布地址"一行
- 如果 TunnelService 有 URL 就显示，没有就显示"未开启"

### 阶段 2 不做的

- 不重构 Dashboard 布局（阶段 3-6）
- 不重写历史/统计页（阶段 7-8）
- 不实现操作人登记流程（阶段 4）
- 不重做 Web 状态发布页（阶段 5）
- 不改造 ProcessDetector 为完整配置化（阶段 3）
- 不新增操作人相关的 API 端点（阶段 4-5）
- 不删除任何现有文件或功能

## 风险

| 风险 | 缓解 |
|------|------|
| ALTER TABLE 在已有数据库上可能失败 | 用 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`（SQLite 不支持 IF NOT EXISTS for ALTER）→ 需要用 try-catch 或先查 schema |
| ProcessDetector 返回值改动影响调用方 | RemoteMonitorService 是唯一调用方，改动范围可控 |
| API 注册后可能端口冲突 | Kestrel 默认绑定 8000，与 Python 可能冲突；加 try-catch 降级到随机端口 |
| 现有 `computerStatus: "idle"` 语义被 API 消费者依赖 | 只新增状态值不改已有值的含义；API 保持向后兼容 |
| WPF BlazorWebView 中运行 Kestrel 可能有线程问题 | Kestrel 在独立线程运行（已有 _api_thread 模式），确保 DI ServiceProvider 共享 |

## 本阶段未改代码

阶段 1 只做了审计和报告，未修改任何功能文件。仅更新了 `findings.md`。
