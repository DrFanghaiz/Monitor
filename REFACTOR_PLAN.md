# Monitor 项目重构目录方案

## 目标

本次重构采用“桌面单体不拆部署，先做代码分层”的路线。

目标不是马上改成独立前后端，而是先把当前项目中混在一起的 UI、业务逻辑、状态聚合、数据访问拆开，为后续维护、测试、Web 扩展、以及未来可能的前后端拆分做准备。

## 核心结论

- 当前项目暂时不建议直接拆成独立前端 + 独立后端部署。
- 当前最值得做的是“代码分层解耦”。
- 推荐先形成清晰的 `UI -> Service -> Repository -> Infrastructure` 分层。
- Web 页面应视为附属访问层，不应继续直接依赖 GUI 回调取状态。

## 重构原则

1. UI 不直接访问数据库。
2. UI 不直接调用底层监控、隧道、配置细节。
3. 所有业务动作统一经过 services。
4. 所有持久化统一经过 repositories。
5. Web server 不再回调 GUI，而是调用统一的 status service。
6. 优先保持行为不变，先重构结构，再逐步迁移实现。
7. 每个阶段结束后都必须保证程序可运行。

---

## 目标目录结构

```text
Monitor/
├─ main.py
├─ app_bootstrap.py
├─ requirements.txt
├─ config.json
├─ monitor.db
├─ web/
│  └─ index.html
├─ backups/
├─ build/
├─ dist/
├─ legacy/
│  ├─ timer_legacy.py
│  └─ timer_backup.py
├─ app/
│  ├─ __init__.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ constants.py
│  │  ├─ paths.py
│  │  ├─ exceptions.py
│  │  ├─ models.py
│  │  └─ utils.py
│  ├─ infrastructure/
│  │  ├─ __init__.py
│  │  ├─ config/
│  │  │  ├─ __init__.py
│  │  │  └─ config_manager.py
│  │  ├─ database/
│  │  │  ├─ __init__.py
│  │  │  ├─ connection.py
│  │  │  ├─ schema.py
│  │  │  └─ migration.py
│  │  ├─ logging/
│  │  │  ├─ __init__.py
│  │  │  └─ app_logger.py
│  │  ├─ system/
│  │  │  ├─ __init__.py
│  │  │  ├─ instance_lock.py
│  │  │  ├─ tray_manager.py
│  │  │  └─ process_detector.py
│  │  └─ security/
│  │     ├─ __init__.py
│  │     └─ password_manager.py
│  ├─ domain/
│  │  ├─ __init__.py
│  │  ├─ entities/
│  │  │  ├─ __init__.py
│  │  │  ├─ usage_record.py
│  │  │  ├─ reservation.py
│  │  │  ├─ remote_session.py
│  │  │  └─ app_status.py
│  │  ├─ repositories/
│  │  │  ├─ __init__.py
│  │  │  ├─ usage_repository.py
│  │  │  ├─ reservation_repository.py
│  │  │  ├─ remote_session_repository.py
│  │  │  ├─ audit_repository.py
│  │  │  └─ settings_repository.py
│  │  └─ services/
│  │     ├─ __init__.py
│  │     ├─ timer_service.py
│  │     ├─ reservation_service.py
│  │     ├─ statistics_service.py
│  │     ├─ status_service.py
│  │     ├─ remote_monitor_service.py
│  │     ├─ web_access_service.py
│  │     ├─ backup_service.py
│  │     └─ tunnel_service.py
│  ├─ presentation/
│  │  ├─ __init__.py
│  │  ├─ desktop/
│  │  │  ├─ __init__.py
│  │  │  ├─ app_window.py
│  │  │  ├─ theme.py
│  │  │  ├─ viewmodels/
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ timer_viewmodel.py
│  │  │  │  ├─ history_viewmodel.py
│  │  │  │  ├─ statistics_viewmodel.py
│  │  │  │  ├─ reservation_viewmodel.py
│  │  │  │  └─ settings_viewmodel.py
│  │  │  ├─ frames/
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ sidebar_frame.py
│  │  │  │  ├─ timer_frame.py
│  │  │  │  ├─ compact_frame.py
│  │  │  │  ├─ history_frame.py
│  │  │  │  ├─ statistics_frame.py
│  │  │  │  ├─ reservation_frame.py
│  │  │  │  └─ settings_frame.py
│  │  │  └─ components/
│  │  │     ├─ __init__.py
│  │  │     ├─ dialogs.py
│  │  │     ├─ toasts.py
│  │  │     └─ widgets.py
│  │  └─ web/
│  │     ├─ __init__.py
│  │     ├─ server.py
│  │     ├─ auth.py
│  │     └─ dto.py
│  ├─ adapters/
│  │  ├─ __init__.py
│  │  ├─ charts/
│  │  │  ├─ __init__.py
│  │  │  └─ chart_drawer.py
│  │  ├─ avatar/
│  │  │  ├─ __init__.py
│  │  │  └─ avatar_service.py
│  │  └─ backup/
│  │     ├─ __init__.py
│  │     └─ backup_manager.py
│  └─ tests/
│     ├─ __init__.py
│     ├─ unit/
│     │  ├─ test_timer_service.py
│     │  ├─ test_reservation_service.py
│     │  ├─ test_status_service.py
│     │  └─ test_remote_monitor_service.py
│     └─ integration/
│        ├─ test_database_usage.py
│        ├─ test_web_status_api.py
│        └─ test_config_manager.py
└─ scripts/
   ├─ build_exe.py
   └─ dev_migrate_legacy.py
```

---

## 各层职责说明

## 1. `main.py`

只做程序入口，不承载业务逻辑。

职责：

- 初始化应用
- 调用 `app_bootstrap.py`
- 启动桌面主循环
- 处理顶层异常

## 2. `app_bootstrap.py`

新的装配中心，负责把对象实例组织起来。

职责：

- 创建配置对象
- 创建数据库连接和 repositories
- 创建 services
- 创建桌面窗口
- 创建 Web server
- 注册关闭钩子

这个文件用于替代当前 `timer.py` 中“大总控 + 大杂烩”的启动职责。

## 3. `app/core/`

放基础定义，不放具体业务实现。

建议内容：

- `constants.py`：状态枚举、默认端口、主题常量
- `paths.py`：配置、数据库、备份等路径
- `exceptions.py`：业务异常，如预约冲突、认证失败
- `models.py`：通用 dataclass / enum
- `utils.py`：时间格式化、字符串工具

## 4. `app/infrastructure/`

放技术实现细节。

### `config/config_manager.py`

替代当前 `config.py`。

职责：

- 加载和保存配置
- 合并默认配置
- 暴露配置访问接口

### `database/`

拆分当前 `database.py` 的大文件模式。

建议拆为：

- `connection.py`：数据库连接管理
- `schema.py`：建表 SQL
- `migration.py`：历史 txt 数据迁移

### `logging/app_logger.py`

收口日志能力，避免日志实现散落。

### `system/`

放系统集成能力：

- `instance_lock.py`
- `tray_manager.py`
- `process_detector.py`

说明：

- `remote_monitor.py` 中的进程扫描逻辑建议下沉到 `process_detector.py`
- 这样 service 层不直接依赖 `subprocess`

### `security/password_manager.py`

保留密码管理逻辑，但不要让 UI 直接依赖配置实现细节。

## 5. `app/domain/entities/`

放核心业务实体，建议统一使用 dataclass。

建议实体：

- `UsageRecord`
- `Reservation`
- `RemoteSession`
- `AppStatus`

要求：

- 业务层和 UI 层尽量传实体，不直接传裸 dict

## 6. `app/domain/repositories/`

每个 repository 只负责一类数据。

### `usage_repository.py`

职责：

- 添加使用记录
- 查询使用记录
- 删除记录
- 提供用户统计基础查询

### `reservation_repository.py`

职责：

- 查询预约
- 新增预约
- 检查预约冲突
- 取消预约

### `remote_session_repository.py`

职责：

- 开始远程会话
- 结束远程会话
- 查询活跃会话
- 查询最近会话

### `audit_repository.py`

职责：

- 写审计日志
- 查询审计日志

### `settings_repository.py`

说明：

- 可作为后续扩展预留
- 当前如果不需要落库配置，可先不完全实现

要求：

- repository 返回实体或明确 DTO
- 不直接把 SQLite row 往上透传

## 7. `app/domain/services/`

这是本次重构的核心。

### `timer_service.py`

从当前计时界面中抽出计时业务逻辑。

职责：

- 开始计时
- 停止计时
- 获取当前本地使用状态
- 校验用户输入
- 落库使用记录

要求：

- 不依赖 Tkinter 控件
- 不直接操作 label、button 等 UI 对象

### `reservation_service.py`

从预约界面中抽业务逻辑。

职责：

- 获取指定日期预约
- 新建预约
- 冲突检查
- 取消预约
- 时间段合法性校验

### `statistics_service.py`

从 `charts.py` 和 `database.py` 抽统计计算逻辑。

职责：

- 用户统计
- 小时分布
- 每日趋势
- 图表所需数据准备

要求：

- 只产出数据
- 不负责画图

### `status_service.py`

这是最关键的统一状态入口。

职责：

- 聚合本地使用状态
- 聚合远程控制状态
- 聚合今日预约
- 聚合今日记录
- 为 GUI 和 Web 提供统一状态对象

要求：

- 替代当前 GUI 自取 + Web 回调取数的分散模式

### `remote_monitor_service.py`

从 `remote_monitor.py` 抽成业务服务。

职责：

- 启停监控线程
- 识别远程控制工具
- 维护当前远程状态
- 落库远程会话

### `web_access_service.py`

处理 Web 访问鉴权。

职责：

- Web 登录认证
- token 生成与校验
- token 生命周期管理
- Web 接口访问控制

### `backup_service.py`

职责：

- 触发备份
- 清理过期备份
- 封设备份流程

### `tunnel_service.py`

从 `tunnel.py` 抽成服务。

职责：

- 启停 tunnel
- 获取公网地址
- 返回 tunnel 状态
- 封装 `cloudflared` / `ngrok` 差异

## 8. `app/presentation/desktop/`

这是桌面 UI 层，只负责展示和交互，不承载底层业务。

### `app_window.py`

替代当前 `App(ctk.CTk)` 的总装配角色。

职责：

- 创建主窗口
- 切换页面
- 绑定 viewmodel
- 注册关闭事件

### `theme.py`

抽离当前分散在多个文件里的字体、颜色、尺寸常量。

### `viewmodels/`

建议增加 viewmodel 层，降低 frame 和 service 的耦合。

职责：

- 把 service 输出转换成 UI 易消费的数据
- 处理页面交互事件
- 做轻量状态缓存

建议文件：

- `timer_viewmodel.py`
- `history_viewmodel.py`
- `statistics_viewmodel.py`
- `reservation_viewmodel.py`
- `settings_viewmodel.py`

### `frames/`

将当前大文件中的多个 frame 按“一类一文件”拆开：

- `sidebar_frame.py`
- `timer_frame.py`
- `compact_frame.py`
- `history_frame.py`
- `statistics_frame.py`
- `reservation_frame.py`
- `settings_frame.py`

要求：

- frame 不直接调用 `db`
- frame 不直接调用 `config`
- frame 不直接调用 `remote_monitor`
- frame 不直接调用 `tunnel_manager`
- frame 只通过 viewmodel 或 service 访问业务

## 9. `app/presentation/web/`

这里是 Web 表现层和 HTTP 适配层，不放核心业务。

### `server.py`

替代当前 `web_server.py`。

职责：

- 定义 HTTP 路由
- 调用 `web_access_service`
- 调用 `status_service`
- 返回 JSON 和静态页

### `auth.py`

封装 token 相关实现。

### `dto.py`

定义 Web 接口的输入输出结构。

关键要求：

- 不再依赖 GUI 注册回调获取本地状态
- 统一通过 `status_service` 提供状态

## 10. `app/adapters/`

放外部表现或第三方能力适配。

### `charts/chart_drawer.py`

保留图表绘制能力，但只接收统计数据。

职责分工：

- `statistics_service` 负责准备数据
- `chart_drawer` 负责绘制 matplotlib 图表

### `avatar/`

处理头像生成与缓存。

### `backup/`

放偏工具化的备份实现。

## 11. `app/tests/`

本次即使不补全所有测试，也建议先把测试结构建立起来。

优先级最高的测试：

- `test_timer_service.py`
- `test_reservation_service.py`
- `test_status_service.py`
- `test_remote_monitor_service.py`
- `test_web_status_api.py`

---

## 当前文件迁移建议

以下清单可直接作为迁移对照表。

### 保留但迁移 / 拆分

- `timer.py`
  - 目标：逐步拆空
  - 最终保留为 `legacy/timer_legacy.py` 或删除
- `database.py`
  - 拆到 `app/infrastructure/database/` 和 `app/domain/repositories/`
- `config.py`
  - 迁到 `app/infrastructure/config/config_manager.py`
- `remote_monitor.py`
  - 迁到 `app/domain/services/remote_monitor_service.py`
  - 进程检测下沉到 `app/infrastructure/system/process_detector.py`
- `web_server.py`
  - 迁到 `app/presentation/web/server.py`
- `tunnel.py`
  - 迁到 `app/domain/services/tunnel_service.py`
- `reservation.py`
  - UI 留在 `app/presentation/desktop/frames/reservation_frame.py`
  - 业务挪到 `app/domain/services/reservation_service.py`
- `charts.py`
  - 绘图逻辑迁到 `app/adapters/charts/chart_drawer.py`
  - 统计数据准备迁到 `statistics_service.py`
- `tray.py`
  - 迁到 `app/infrastructure/system/tray_manager.py`
- `password_manager.py`
  - 迁到 `app/infrastructure/security/password_manager.py`
- `backup.py`
  - 业务迁到 `backup_service.py`
  - 工具化实现迁到 `app/adapters/backup/backup_manager.py`
- `avatar.py`
  - 迁到 `app/adapters/avatar/avatar_service.py`
- `instance_lock.py`
  - 迁到 `app/infrastructure/system/instance_lock.py`

---

## 分阶段执行方案

不要一次性推倒重来，建议按以下五个阶段执行。

## 第一阶段：搭目录，不改行为

目标：

- 建立 `app/` 分层目录
- 新增 `main.py`、`app_bootstrap.py`
- 把旧文件迁入新目录或建立兼容 wrapper
- 保证程序仍然可以运行

交付标准：

- 启动方式切换为 `main.py`
- 行为不变

## 第二阶段：抽数据访问层

目标：

- 拆分 `database.py`
- 建立 repositories
- 逐步让 UI 不再依赖数据库大对象

交付标准：

- 预约、历史、统计、远程会话均通过 repository 访问

## 第三阶段：抽 service 层

目标：

- 建立 `timer_service`
- 建立 `reservation_service`
- 建立 `status_service`
- 建立 `remote_monitor_service`
- 建立 `tunnel_service`

交付标准：

- frame 层不再直接调用 `db/config/remote_monitor/tunnel`

## 第四阶段：拆 UI 文件

目标：

- 将 `timer.py` 中多个 frame 类拆成独立文件
- 引入 `theme.py`
- 引入 viewmodel

交付标准：

- `timer.py` 不再是超大文件
- 各页面职责清楚

## 第五阶段：统一 Web 状态入口

目标：

- 重写 Web server 对状态的依赖关系
- 去掉 GUI 回调注入模式
- 改为统一由 `status_service` 提供状态

交付标准：

- Web 和桌面共用同一套状态聚合逻辑
- 为未来可能的独立后端预留天然边界

---

## 给执行者的强约束

以下要求建议严格执行：

1. 不允许先做技术换血，例如先换 Web 框架、数据库、桌面框架。
2. 不允许在重构过程中顺手改产品行为。
3. 第一轮只做结构迁移和解耦，不改 UI 风格和交互设计。
4. 每个阶段结束都必须保证程序可运行。
5. `status_service` 必须成为桌面和 Web 的统一状态来源。
6. frame 层不得直接访问 SQLite、配置文件、远程监控器、隧道管理器。
7. `timer.py` 必须逐步拆空，最终仅保留 legacy 参考或完全移除。
8. 如果无法一次迁完，可以加兼容适配层，但要标注 `TODO remove legacy adapter`。
9. 每阶段都要输出变更摘要、未迁移项、风险点、下一阶段计划。
10. 避免为了分层而过度抽象，优先可维护和可落地。

---

## 最小可行版本目录

如果希望先低风险落地，可先采用精简版结构：

```text
Monitor/
├─ main.py
├─ app_bootstrap.py
├─ app/
│  ├─ core/
│  ├─ infrastructure/
│  │  ├─ config/
│  │  ├─ database/
│  │  ├─ logging/
│  │  └─ system/
│  ├─ services/
│  │  ├─ timer_service.py
│  │  ├─ reservation_service.py
│  │  ├─ status_service.py
│  │  ├─ remote_monitor_service.py
│  │  └─ tunnel_service.py
│  ├─ ui/
│  │  ├─ app_window.py
│  │  ├─ theme.py
│  │  └─ frames/
│  └─ web/
│     └─ server.py
```

说明：

- 这个版本更适合第一轮
- 足够把关键耦合拆开
- 后续再逐步升级到完整版目录

---

## 推荐执行顺序

建议执行者只先完成前三阶段：

1. 第一阶段：搭目录，不改行为
2. 第二阶段：抽数据访问层
3. 第三阶段：抽 service 层

原因：

- 这三步已经能显著降低耦合
- 风险相对可控
- 也便于后续审查

等前三阶段稳定后，再继续拆 UI 和统一 Web 状态入口。

---

## 最终预期效果

完成本轮重构后，项目应达到以下状态：

- 桌面 UI 不再直接操作数据库和底层系统模块
- Web 状态接口不再依赖 GUI 回调
- 核心业务逻辑沉淀到 services
- 数据访问统一沉淀到 repositories
- `timer.py` 超大文件问题被持续拆解
- 后续若要拆成独立前后端，将具备较低迁移成本
