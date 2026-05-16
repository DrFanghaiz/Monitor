# Monitor 远程占用监控实施指南

这份文档用于指导后续开发。可以交给 DeepSeek V4 Pro 或其他代码模型执行，但执行前必须先阅读 `PRODUCT.md`、`DESIGN.md`、`task_plan.md`、`findings.md` 和本文件。

## 一、目标重述

Monitor 要解决的问题是：多人远程使用同一台 Windows 公用机器时，如何避免同时连接、互相抢控制权。

最终用户流程应该是：

1. 使用者准备远程连接机器。
2. 使用者先打开 Monitor 发布的网址。
3. 网页显示机器当前状态：空闲、使用中、未知或异常。
4. 如果空闲，使用者登记姓名并开始使用，或按团队规则连接机器。
5. 如果使用中，网页显示当前使用者、远程工具、开始时间、持续时间，后来者不应连接。
6. 使用结束后，系统记录结束时间和持续时长。

## 二、必须先审计的现有文件

优先阅读这些文件，确认现有能力再修改：

- `src/Monitor.App/Services/RemoteMonitorService.cs`
- `src/Monitor.App/Infrastructure/System/ProcessDetector.cs`
- `src/Monitor.App/Services/StatusService.cs`
- `src/Monitor.App/Services/TimerService.cs`
- `src/Monitor.App/Models/RemoteSession.cs`
- `src/Monitor.App/Models/AppStatus.cs`
- `src/Monitor.App/Repositories/IRemoteSessionRepository.cs`
- `src/Monitor.App/Repositories/RemoteSessionRepository.cs`
- `src/Monitor.App/Infrastructure/Database/SchemaInitializer.cs`
- `src/Monitor.App/Api/StatusEndpoints.cs`
- `src/Monitor.App/Api/TimerEndpoints.cs`
- `src/Monitor.App/Api/SettingsEndpoints.cs`
- `src/Monitor.App/Services/WebAccessService.cs`
- `src/Monitor.App/Services/TunnelService.cs`
- `src/Monitor.App/Components/Pages/Dashboard.razor`
- `src/Monitor.App/Components/Pages/History.razor`
- `src/Monitor.App/Components/Pages/Statistics.razor`
- `src/Monitor.App/Components/Pages/Settings.razor`

## 三、核心状态模型

新增或重构一个统一的远程占用状态，不要把它混在普通手动计时里。

建议状态：

- `Idle`：未检测到远程控制会话，且检测服务正常。
- `Occupied`：检测到远程控制会话，已有关联操作人或待确认操作人。
- `Unknown`：检测失败、检测服务关闭、数据过期或无法确认。
- `Error`：检测服务异常、配置错误或数据库写入失败。

建议字段：

- `Status`
- `RemoteTool`
- `OperatorName`
- `StartedAt`
- `EndedAt`
- `DurationSeconds`
- `LastSeenAt`
- `Source`
- `Confidence`
- `Message`

注意：`Confidence` 不是用来做模糊兜底，而是让界面明确表达“进程存在但是否正在控制仍需确认”。不能用它把未知状态伪装为空闲。

## 四、远程软件检测规则

不要直接写死一个进程名就完事。远程软件通常有后台常驻进程，必须区分：

- 后台服务存在。
- 客户端打开。
- 正在远程控制。
- 被远程连接中。

建议实现：

1. 建立 `RemoteToolSignature` 配置结构。
2. 每个工具包含：
   - 工具名。
   - 进程名候选。
   - 可选窗口标题规则。
   - 可选端口或连接信号。
   - 是否启用。
3. 默认支持向日葵、ToDesk、AnyDesk。
4. 设置页允许管理员调整检测规则。
5. 检测结果必须写明来源，例如 `process`, `window`, `manual_claim`。

验收标准：

- 只开机但无人远程控制时，不应轻易显示“使用中”。
- 检测不确定时显示“状态未知，需要确认”。
- 检测到明确远程占用时，首页和网页端必须同步显示“使用中”。

## 五、操作人识别方案

系统无法稳定从远程软件自动知道操作人，因此必须设计显式流程。

推荐方案：

1. 网页端提供“登记使用”入口。
2. 使用者输入姓名后，状态变为“已登记，准备连接”或“使用中”。
3. 本机检测到远程控制软件活跃后，把该登记人与远程会话关联。
4. 如果检测到远程占用但没有登记人，状态显示“使用中，操作人未确认”。
5. 本机端允许管理员补录或修正操作人。

不要做：

- 不要假设 Windows 当前登录用户名就是远程操作人。
- 不要在没有登记人的情况下把历史记录写成“未知”后就不管。

## 六、Web 发布页

Web 页第一屏只回答一个问题：现在能不能连接这台机器？

页面结构建议：

- 大状态：空闲 / 使用中 / 状态未知 / 异常。
- 当前机器名。
- 当前使用者。
- 远程工具。
- 开始时间。
- 已使用时长。
- 最近更新时间。
- 操作按钮：登记使用、刷新状态。
- 如果使用中，显示明确提示：请勿连接，当前有人使用。

Web 端不应默认展示复杂统计、完整历史和设置。

API 建议：

- `GET /api/status/public`
- `POST /api/occupancy/claim`
- `POST /api/occupancy/release`
- `GET /api/occupancy/history`

如果已有 API，可以复用，但命名和返回结构要围绕远程占用，不要继续围绕 timer。

## 七、本机端 UI 重构

首页改名建议：

- 从“控制台”调整为“远程占用监控”或保留“控制台”，但第一模块必须是远程状态。

首页优先级：

1. 当前远程占用状态。
2. 当前使用者和远程工具。
3. 开始时间和持续时间。
4. Web 发布地址和复制入口。
5. 最近远程使用记录。
6. 手动补录或修正操作人。

手动计时页面可以保留，但应降级为辅助工具，不能让用户误以为这是主流程。

## 八、历史记录重构

历史记录主表应围绕远程会话：

- 操作人。
- 远程工具。
- 开始时间。
- 结束时间。
- 持续时长。
- 结束原因。
- 状态来源。
- 是否异常结束。

删除记录必须二次确认。

## 九、统计页重构

统计页不要再以普通用户使用分布为主。

建议指标：

- 今日远程占用次数。
- 当前占用时长。
- 近 30 天总占用时长。
- 最常用远程工具。
- 最常使用者。
- 高峰时段。
- 异常结束次数。

图表建议：

- 每日远程占用时长折线图。
- 操作人占用时长排行。
- 远程工具使用占比。
- 小时热力图或高峰条形图。

## 十、设置页补齐

设置项建议：

- Web 发布是否启用。
- Web 端口。
- 发布地址显示。
- 访问密码。
- 状态刷新间隔。
- 远程检测是否启用。
- 远程软件检测规则。
- 状态过期时间。
- 未登记占用如何处理。
- 自动备份。

## 十一、数据库调整

优先检查现有 `remote_sessions` 表能否满足需求。

如果不足，增加字段时必须走 schema initializer，不要手动改数据库文件。

建议字段：

- `operator_name`
- `remote_tool`
- `start_time`
- `end_time`
- `duration_seconds`
- `status`
- `source`
- `last_seen_at`
- `end_reason`
- `created_at`

如果现有字段已有同义字段，优先复用，避免无意义迁移。

## 十二、验收清单

必须满足：

- 空闲时，网页端明确显示“空闲，可以连接”。
- 使用中，网页端明确显示“请勿连接，当前有人使用”。
- 使用中显示操作人、远程工具、开始时间、持续时长。
- 检测失败时显示“状态未知”，不能显示空闲。
- 历史记录能看到远程使用开始和结束。
- 删除历史记录有确认。
- 设置页能看到 Web 发布地址和远程检测开关。
- 本机端和网页端状态一致。

## 十三、推荐执行顺序

1. 审计现有远程检测和 Web 发布代码。
2. 定义远程占用状态模型。
3. 先打通 `GET /api/status/public`。
4. 重做 Web 状态页。
5. 接入远程检测服务。
6. 接入操作人登记。
7. 重构本机首页。
8. 重构历史和统计。
9. 补齐设置页。
10. 做真实远程工具测试。

## 十四、给代码模型的注意事项

- 不要一次性大改所有页面。
- 每个阶段都要构建验证。
- 不要删除用户已有数据。
- 不要把检测失败当作空闲。
- 不要把手动计时继续放在主路径。
- 不要使用含糊文案，例如“安全”，应写清楚“未检测到远程占用”。
- 不要绕开现有 Repository 和 Service 分层。
- 不要直接硬编码所有检测规则，至少要集中配置，后续可维护。
