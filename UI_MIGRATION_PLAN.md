# Monitor 高颜值 UI 迁移方案

## 目标

当前项目已经完成了 service / repository / status 聚合层的重构，业务解耦基础已经具备。

如果目标是“非常好看”的 UI，而不是在 `customtkinter` 上继续做有限美化，那么建议项目进入下一阶段：

**保留 Python 业务层，重做 UI 层为现代前端，并使用桌面壳集成。**

推荐目标架构：

- 前端：React + Vite + TypeScript
- 视觉层：Tailwind CSS + 自定义 design tokens
- 动效：Framer Motion
- 图表：ECharts
- 后端：FastAPI
- 桌面壳：pywebview

该方案不是传统云端“前后端网站”，而是：

**前端 UI + Python 本地服务 + 桌面壳**

---

## 结论

### 为什么现在值得迁移

当前项目已经完成：

- `timer_service`
- `reservation_service`
- `statistics_service`
- `status_service`
- `remote_monitor_service`
- `tunnel_service`
- `web_access_service`

并且 Web 状态入口已经服务化。

这意味着：

- 核心业务逻辑已经基本脱离 GUI
- 数据访问已经开始通过 repository 收口
- UI 已经不再是系统的唯一真实状态源

所以现在迁 UI，不需要推倒业务层，只需要：

1. 新增 API 层
2. 新建前端
3. 用新前端替换 `customtkinter` 表现层

---

## 总体架构

建议目标目录结构如下：

```text
Monitor/
├─ main.py
├─ timer.py
├─ desktop/
│  ├─ __init__.py
│  └─ shell.py
├─ backend/
│  ├─ __init__.py
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ app.py
│  │  ├─ deps.py
│  │  ├─ schemas.py
│  │  └─ routes/
│  │     ├─ __init__.py
│  │     ├─ status.py
│  │     ├─ timer.py
│  │     ├─ reservation.py
│  │     ├─ statistics.py
│  │     ├─ settings.py
│  │     └─ auth.py
│  ├─ services/
│  ├─ repositories/
│  ├─ infrastructure/
│  └─ adapters/
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ tsconfig.json
│  ├─ index.html
│  ├─ public/
│  └─ src/
│     ├─ main.tsx
│     ├─ app/
│     │  ├─ App.tsx
│     │  ├─ router.tsx
│     │  └─ providers.tsx
│     ├─ pages/
│     │  ├─ Dashboard.tsx
│     │  ├─ Timer.tsx
│     │  ├─ History.tsx
│     │  ├─ Statistics.tsx
│     │  ├─ Reservation.tsx
│     │  └─ Settings.tsx
│     ├─ layout/
│     │  ├─ AppShell.tsx
│     │  ├─ Sidebar.tsx
│     │  ├─ Topbar.tsx
│     │  └─ StatusRail.tsx
│     ├─ components/
│     │  ├─ ui/
│     │  ├─ charts/
│     │  ├─ timer/
│     │  ├─ history/
│     │  ├─ reservation/
│     │  └─ settings/
│     ├─ features/
│     │  ├─ status/
│     │  ├─ timer/
│     │  ├─ history/
│     │  ├─ statistics/
│     │  ├─ reservation/
│     │  └─ settings/
│     ├─ services/
│     │  ├─ api.ts
│     │  ├─ status.ts
│     │  ├─ timer.ts
│     │  ├─ reservation.ts
│     │  ├─ statistics.ts
│     │  └─ settings.ts
│     ├─ hooks/
│     ├─ theme/
│     │  ├─ tokens.css
│     │  ├─ tailwind-theme.ts
│     │  └─ motion.ts
│     ├─ styles/
│     │  ├─ globals.css
│     │  └─ utilities.css
│     └─ types/
└─ legacy/
```

---

## 推荐技术栈

## 1. 前端

- `React`
- `Vite`
- `TypeScript`

理由：

- 最强的 UI 生态
- 适合做复杂页面
- 更容易做出高质量视觉
- 适合桌面壳集成

## 2. 样式系统

- `Tailwind CSS`
- 自定义 design tokens

要求：

- 不允许直接套默认组件库风格
- 可以参考 `shadcn/ui` 的结构方式，但必须重做主题
- 必须建立自己的颜色、半径、阴影、间距、字重体系

## 3. 动效

- `Framer Motion`

适用场景：

- 登录页过渡
- 仪表盘卡片进入
- 页面切换
- 状态变化
- 悬浮反馈

## 4. 图表

- `ECharts`

理由：

- 更适合“高级数据面板”
- 热力图、趋势图、分布图能力强
- 可以统一图表风格

## 5. API 层

- `FastAPI`

理由：

- 当前 Python service 层易于封装成 API
- 类型清晰
- 路由边界清晰
- 后续桌面和 Web 都能共用

## 6. 桌面壳

优先：

- `pywebview`

理由：

- 成本最低
- 最容易和 Python 服务集成
- 适合本地服务 + 本地 UI 的桌面应用模型

次选：

- `Tauri`

不建议首选：

- `Electron`

---

## 视觉方向

这次迁移的目标不是“更像后台”，而是“更像成熟产品”。

建议统一视觉方向为：

**深色控制台 + 雾面数据面板 + 青蓝信号高亮**

### 关键词

- 冷静
- 精致
- 科技感
- 控制中心
- 状态感
- 数据可视化统一

### 视觉原则

1. 不使用纯黑和纯白。
2. 状态色必须有明确语义：
   - 青蓝：主要交互 / 当前活跃
   - 绿色：正常 / 空闲 / 成功
   - 红色：远程控制 / 停止 / 风险
   - 琥珀：警告 / 预约中 / 待处理
3. 计时页要有沉浸感，不能只是“大数字 + 按钮”。
4. 卡片层次通过背景、边框、柔和阴影与间距体现，不靠重度玻璃拟态。
5. 图表页必须有统一主题，不允许“每张图各长各的”。
6. 文本层级必须强，标题、标签、数值、说明要有明显差异。
7. 动效要克制，不做廉价弹跳。

---

## 页面方案

## 1. Dashboard

作为新首页，不再默认直接进入姓名输入框。

建议模块：

- 当前机器状态
- 当前使用者
- 当前计时状态
- 远程控制状态
- 今日总使用时长
- 今日预约概览
- 最近记录
- 快捷开始计时入口

目标：

- 打开就能看清系统状态
- 具备“控制中心”气质

## 2. Timer

这是视觉核心页，必须做到最强。

建议模块：

- 中央超大计时器
- 当前用户头像和姓名
- 会话状态
- 开始 / 停止主操作
- 会话信息
- 悬浮窗入口

目标：

- 沉浸
- 聚焦
- 高级
- 一眼可识别

## 3. History

建议模块：

- 搜索与筛选
- 历史记录流
- 时长可视条
- 批量选择
- 删除操作

目标：

- 不像传统后台表格
- 依旧保持数据密度
- 更有节奏和可读性

## 4. Statistics

建议模块：

- 顶部 KPI
- 图表类型切换
- 用户分布
- 趋势
- 热力图
- 高频使用时段

目标：

- 数据图表统一主题
- 仪表盘级观感
- 不只是“matplotlib 截图感”

## 5. Reservation

建议模块：

- 左侧日期导航
- 右侧时间槽
- 当前时段状态标签
- 新建预约侧栏 / 抽屉

目标：

- 像调度界面
- 时间槽层次清晰
- 高可读性

## 6. Settings

建议模块：

- 管理员密码
- Web 访问密码
- 备份与恢复
- 隧道配置
- 系统信息

目标：

- 分组明确
- 不显杂乱
- 更像系统面板而不是“按钮堆”

---

## 后端 API 设计

建议新增 API 层，对现有 service 做接口封装。

## 核心接口

### 状态

- `GET /api/status`
- `GET /api/status/sidebar`

### 计时

- `POST /api/timer/start`
- `POST /api/timer/stop`
- `GET /api/timer/state`
- `GET /api/timer/history`
- `DELETE /api/timer/history/{id}`
- `POST /api/timer/history/delete-batch`

### 预约

- `GET /api/reservations`
- `POST /api/reservations`
- `POST /api/reservations/{id}/cancel`

### 统计

- `GET /api/statistics/users`
- `GET /api/statistics/hourly`
- `GET /api/statistics/daily`
- `GET /api/statistics/distribution`

### 设置

- `GET /api/settings`
- `POST /api/settings/password/admin`
- `POST /api/settings/password/web`
- `POST /api/settings/backup`
- `GET /api/settings/backups`

### 认证

- `POST /api/auth`

---

## 前端实现原则

## 页面组织

建议按 feature 组织，而不是全局扁平堆文件。

每个 feature 至少包含：

- API 调用
- 类型定义
- 页面级组件
- 局部 hooks

## 状态管理

建议：

- `React Query` 管服务端状态
- 本地 UI 状态使用组件 state 或轻量 store

避免：

- 一开始就上复杂全局状态库

## 设计系统

必须先建立 tokens：

- 颜色
- 间距
- 圆角
- 阴影
- 字号
- 字重
- 动效时长
- 图表色板

不得直接在组件中到处硬编码颜色值。

---

## 迁移阶段

不要一次重写完，建议按 4 个阶段执行。

## 阶段一：新增 API 层

目标：

- 建 `backend/api/`
- 用 FastAPI 封装现有 service
- 不改业务逻辑
- 先提供最小接口集

交付：

- `GET /api/status`
- `POST /api/timer/start`
- `POST /api/timer/stop`
- `GET /api/timer/history`
- `GET /api/statistics/users`

要求：

- 不允许在 route 内写业务逻辑
- route 只调用 service

## 阶段二：搭前端骨架

目标：

- 初始化 `frontend/`
- 建 layout
- 建 design tokens
- 建 API client
- 建 Dashboard + Timer 页

交付：

- 能本地跑前端
- 能调用 Python API
- 新 UI 初版可访问

要求：

- 先做视觉骨架和主流程
- 不要先做所有页面

## 阶段三：补齐业务页

目标：

- 做 History
- 做 Statistics
- 做 Reservation
- 做 Settings

交付：

- 前端覆盖原桌面主要能力

要求：

- 图表主题统一
- 预约页不允许继续保持传统堆叠按钮样式

## 阶段四：接桌面壳

目标：

- 用 `pywebview` 承载前端
- Python 启动本地 API
- 逐步退出 `customtkinter`

交付：

- 新桌面壳可运行
- 主流程用新 UI
- 旧 `customtkinter` 只保留兼容入口

---

## 最小可行版本

如果要先验证路线，建议先做 MVP：

### 只迁两个页面

- Dashboard
- Timer

### 只暴露这些接口

- `GET /api/status`
- `POST /api/timer/start`
- `POST /api/timer/stop`
- `GET /api/timer/history`
- `GET /api/statistics/users`

### 目标

- 先验证新 UI 的质感
- 先验证 React + Python API + pywebview 组合是否顺畅

---

## 风险点

## 1. Python 与前端启动顺序

需要明确：

- 先起 API
- 再起前端壳
- 开发环境与生产环境分别处理

## 2. 托盘 / 单实例 / 悬浮窗

这些能力依旧建议保留在 Python / 桌面壳层，不放在前端实现。

## 3. 状态同步

必须坚持：

- 前端只通过 API 读写状态
- 不自己推断业务状态

## 4. 文本编码

现有部分历史文件已有中文编码混乱现象。

迁移前端时建议：

- 全面统一为 UTF-8
- 避免把旧乱码文本继续带入新界面

---

## 不允许的做法

1. 不允许一边迁前端一边顺手重写业务逻辑。
2. 不允许把 route 写成新的 God Object。
3. 不允许前端直接依赖旧 `customtkinter` 状态。
4. 不允许先做所有页面再统一风格。
5. 不允许默认套 UI 库主题就算完成设计。
6. 不允许只做“更圆一点、更蓝一点”的假升级。

---

## 推荐执行顺序

建议实施顺序：

1. 先搭 API
2. 再搭前端骨架
3. 先做 Dashboard + Timer
4. 再补其余页面
5. 最后接桌面壳

这是风险最低、也最容易尽快看到效果的路线。

---

## 最终预期效果

完成迁移后，项目应达到以下状态：

- Python 负责业务和系统能力
- 前端负责全部视觉和交互
- 桌面应用拥有现代化高质量 UI
- Web 状态页和桌面主界面可共用同一视觉体系
- 后续若继续扩展到纯 Web 版，也具备复用能力

---

## 领导者要求

如果这份方案交给执行者，必须强调：

1. 先保业务稳定，再做 UI 升级。
2. 先做主流程，不要平均用力。
3. 先做 Dashboard + Timer，把视觉质量拉满。
4. 每个阶段结束都必须可运行、可演示。
5. 视觉质量是本次迁移核心目标，不允许只完成“功能对齐”。
6. 所有新前端代码必须围绕统一 design tokens 构建。
7. 组件复用要服务视觉统一，而不是为了抽象而抽象。
8. 任何时候都不要让新前端反向依赖旧桌面状态。
