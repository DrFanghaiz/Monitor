# Monitor 架构改造方案

## 目标

在不推倒重写的前提下，把当前项目从“单体能用”改到“结构清楚、便于迭代、便于发布”。

这份方案只解决结构问题，不改变产品目标：

- 监控本机是否被远程占用
- 记录开始、结束、操作人
- 通过本地界面和公网状态页展示

## 当前架构判断

当前项目本质上是一个单机桌面单体：

- WPF 负责窗口壳
- Blazor Hybrid 负责界面
- Service 负责业务
- Repository 负责 SQLite 读写
- 内嵌 Minimal API 负责网页和外部访问

这个方向本身没错，问题主要是下面 4 个：

1. 页面、业务、外部能力还耦合偏紧
2. 远程检测以后会越堆越乱
3. 状态判断还不够像正式状态机
4. 设置、引导、公网发布还没有形成统一结构

## 改造原则

1. 不改技术栈  
   继续使用 WPF + Blazor Hybrid + SQLite + Dapper

2. 不一步重写  
   采用渐进式改造，每一步都能编译、能运行

3. 先拆边界，再拆目录  
   先把职责分清，再挪文件

4. 不引入多进程  
   当前阶段不拆成桌面程序 + 后台服务两套进程

## 目标结构

建议把 `src/Monitor.App` 逐步收敛到下面的结构：

```text
src/Monitor.App
├─ Host
│  ├─ App.xaml.cs
│  ├─ MainWindow.xaml
│  └─ MainWindow.xaml.cs
├─ UI
│  ├─ Components
│  │  ├─ Layout
│  │  ├─ Pages
│  │  └─ Shared
│  ├─ Styles
│  └─ wwwroot
├─ Application
│  ├─ Abstractions
│  ├─ Status
│  ├─ Timer
│  ├─ Reservation
│  ├─ Remote
│  ├─ Settings
│  └─ Backup
├─ Domain
│  ├─ Models
│  ├─ Enums
│  └─ Rules
├─ Infrastructure
│  ├─ Config
│  ├─ Database
│  ├─ Security
│  ├─ System
│  ├─ Tunnel
│  └─ Repositories
└─ Api
```

## 每层职责

### Host

只做程序启动和关闭：

- 初始化日志
- 初始化数据库
- 注册依赖
- 启动后台任务
- 打开主窗口

不在这一层写业务规则。

### UI

只做界面：

- 显示状态
- 接收点击和输入
- 调用应用层

页面里不要直接写复杂判断，不要直接碰数据库，不要直接碰进程检测。

### Application

这一层以后是项目核心。

它负责：

- 计时流程
- 预约流程
- 远程占用流程
- 设置流程
- 公网发布流程
- 恢复出厂流程
- 首次使用引导流程

这一层只依赖接口，不直接依赖具体实现。

比如：

- `IRemoteDetector`
- `ITunnelGateway`
- `ISettingsStore`
- `IUsageRepository`

### Domain

这一层放真正稳定的核心规则。

例如：

- 远程状态枚举
- 占用状态枚举
- 预约冲突规则
- 操作人登记规则
- 密码最小长度规则

这里不放界面，不放数据库，不放日志。

### Infrastructure

这一层只放外部实现：

- SQLite
- Dapper
- JSON 配置
- cloudflared
- WebView2 外围
- 进程检测
- 文件系统

以后换实现时，主要改这一层。

### Api

只保留接口映射，不放业务逻辑。

API 端点只做：

- 收参数
- 调用应用层
- 返回结果

## 分阶段改造

### 第一阶段：先收 Service 边界

目标：

把当前大的 Service 按业务边界拆清楚，但不大挪目录。

要做：

1. 给 `TimerService`、`ReservationService`、`RemoteMonitorService`、`StatusService` 定义清晰输入输出
2. 把页面里的零散判断移到 Service
3. 把“首次引导”“恢复出厂”“公网配置”这些流程收口到独立服务

完成标准：

- 页面只调用方法，不拼业务规则
- 业务规则不散落在 Razor 页面里

### 第二阶段：把远程检测改成插件式

目标：

解决未来继续接 ToDesk、AnyDesk、TeamViewer 时结构失控的问题。

要做：

定义统一接口：

```csharp
public interface IRemoteDetector
{
    string Name { get; }
    Task<RemoteDetectionResult> DetectAsync(CancellationToken ct);
}
```

然后拆成：

- `SunloginDetector`
- `ToDeskDetector`
- `AnyDeskDetector`
- `TeamViewerDetector`

再增加一个总调度器：

- `RemoteDetectionCoordinator`

完成标准：

- 新增一种远控工具时，不需要去改一个超长的检测类
- 每种检测器可单独测试

### 第三阶段：把状态判断正式改成状态机

目标：

让“空闲 / 本机使用 / 远程占用 / 未知 / 异常”这套状态稳定下来。

建议状态：

- `Idle`
- `LocalUsing`
- `RemoteUsing`
- `Unknown`
- `Error`

要做：

1. 定义统一状态模型
2. 明确进入条件和退出条件
3. 让 UI 和 API 都只读这一个状态结果

完成标准：

- 不会出现“检测坏了却显示空闲”
- 不会出现多处状态文字互相打架

### 第四阶段：统一设置页和首次引导

目标：

把“设置”和“首次使用引导”背后的逻辑统一。

要做：

1. 定义配置完成状态模型
2. 统一以下几项：
   - 管理员密码
   - Web 密码
   - 操作人登记码
   - 公网发布
3. 首次启动按未完成项引导
4. 设置页按同一套状态展示

完成标准：

- 引导和设置页不再两套逻辑
- 任一项是否完成只有一个判断来源

### 第五阶段：拆目录到目标结构

目标：

在业务边界已经稳定后，再正式整理目录。

建议顺序：

1. `Models` 迁到 `Domain`
2. `Repositories`、`Infrastructure/*` 收进 `Infrastructure`
3. `Services` 中真正的业务类迁到 `Application`
4. `Components`、`wwwroot` 收进 `UI`
5. `App.xaml.cs`、`MainWindow` 收进 `Host`

完成标准：

- 文件位置和职责一致
- 新人打开目录能一眼看懂

## 具体建议

### 建议一：保留单进程，不拆双进程

理由：

- 现在安装、发布、排查已经够复杂
- 过早拆成桌面程序 + 后台服务，会明显增加维护成本
- 目前业务规模还没到必须拆的程度

什么时候再考虑双进程：

1. 公网发布必须后台常驻
2. UI 可以关闭但服务必须继续跑
3. 需要托盘常驻
4. 需要无人值守运行

在这之前，不建议拆。

### 建议二：继续用 SQLite + Dapper

理由：

- 轻
- 足够稳
- 适合单机
- 迁移成本低

不建议为了“更高级”而换 ORM。

要做的是补结构：

- 索引
- 约束
- 迁移版本
- 事务

### 建议三：把 UI 设计系统单独收口

建议新增：

- `UI/Styles/Tokens.css`
- `UI/Styles/Components.css`
- `UI/Styles/Layout.css`
- `UI/Styles/Pages.css`

目标不是花哨，而是统一：

- 色板
- 间距
- 圆角
- 字号
- 状态标签
- 表单
- 警告和危险样式

### 建议四：把“可执行动作”统一封成用例

建议后面把这些动作做成明确的应用层用例：

- 开始计时
- 停止计时
- 创建预约
- 删除预约
- 登记操作人
- 创建备份
- 恢复出厂设置
- 配置公网发布

这样以后：

- 页面能调
- API 能调
- 首次引导也能调

不会一套逻辑写三遍。

## 不建议做的事

1. 不建议现在就改成微服务
2. 不建议现在就拆桌面端和后台端
3. 不建议现在就换数据库
4. 不建议为了“整洁”一次性大搬家

这些动作风险大，收益不够高。

## 最推荐的执行顺序

按这个顺序最稳：

1. 收紧现有 Service 职责
2. 远程检测插件化
3. 状态机化
4. 设置与引导统一
5. 目录正式迁移

## 最终目标

改造完成后，项目应达到这几个结果：

1. 页面只管展示
2. 业务规则只有一份
3. 外部能力都在基础设施层
4. 新增远控工具时不改老逻辑
5. 设置、引导、公网发布共用一套配置状态
6. 后续发布和安装流程更稳

## 一句话结论

这套项目最成熟的改法不是推倒重写，而是：

先保持单体，
再把业务、检测、状态、设置这几条主线逐步拆清楚。
