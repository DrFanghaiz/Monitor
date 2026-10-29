using Monitor.App.Models;
using Monitor.App.Repositories;

namespace Monitor.App.Services;

public class StatusService
{
    private readonly TimerService _timer;
    private readonly RemoteMonitorService _remoteMonitor;
    private readonly ComputeMonitorService _computeMonitor;
    private readonly IUsageRepository _usageRepo;
    private readonly IReservationRepository _reservationRepo;

    public StatusService(TimerService timer, RemoteMonitorService remoteMonitor,
        ComputeMonitorService computeMonitor,
        IUsageRepository usageRepo, IReservationRepository reservationRepo)
    {
        _timer = timer;
        _remoteMonitor = remoteMonitor;
        _computeMonitor = computeMonitor;
        _usageRepo = usageRepo;
        _reservationRepo = reservationRepo;
    }

    public AppStatus GetFullStatus()
    {
        var timerState = _timer.GetState();
        var remoteStatus = _remoteMonitor.GetStatus();
        var compute = _computeMonitor.GetStatus();

        // 状态优先级：error > computing > remote_controlled >（检测未知/未就绪按占用）> 检测已关闭 > in_use > idle
        // 失败即安全：检测状态未知或未完成首次扫描时，一律按"占用"保守处理，
        // 宁可让人多确认一次，也不要把"其实不确定"显示成"可连接"。
        string computerStatus;
        if (remoteStatus.Status == "error") computerStatus = "error";
        else if (compute.IsBusy) computerStatus = "computing";
        else if (remoteStatus.IsRemote) computerStatus = "remote_controlled";
        else if (remoteStatus.Status is "unknown" or "initializing") computerStatus = "remote_controlled";
        else if (remoteStatus.Status == "disabled") computerStatus = "unknown";
        else if (timerState.IsRunning) computerStatus = "in_use";
        else computerStatus = "idle";

        var todayStr = DateTime.Now.ToString("yyyy-MM-dd");

        return new AppStatus
        {
            Timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            ComputerStatus = computerStatus,
            LocalUse = new LocalUseInfo
            {
                CurrentUser = timerState.CurrentUser,
                StartTime = timerState.StartTime,
                ElapsedSeconds = timerState.ElapsedSeconds,
                ElapsedFormatted = timerState.ElapsedFormatted
            },
            RemoteControl = new RemoteControlInfo
            {
                IsRemote = remoteStatus.IsRemote,
                RemoteType = remoteStatus.RemoteType,
                StartTime = remoteStatus.StartTime,
                ElapsedSeconds = remoteStatus.ElapsedSeconds,
                ElapsedFormatted = remoteStatus.ElapsedFormatted,
                Status = remoteStatus.Status,
                Source = remoteStatus.Source,
                Confidence = remoteStatus.Confidence,
                OperatorName = remoteStatus.OperatorName,
                LastSeenAt = remoteStatus.LastSeenAt,
                ErrorMessage = remoteStatus.ErrorMessage,
                MatchedSignals = remoteStatus.MatchedSignals,
                Message = remoteStatus.Message,
                RunningTools = remoteStatus.RunningTools,
                ActiveToolCount = remoteStatus.ActiveToolCount,
                Conflict = remoteStatus.Conflict
            },
            Compute = compute,
            TodayRecords = _usageRepo.GetTodayRecords(),
            TodayReservations = _reservationRepo.GetTodayReservations(todayStr)
        };
    }

    public SidebarStatus GetSidebarStatus()
    {
        var remoteStatus = _remoteMonitor.GetStatus();
        var compute = _computeMonitor.GetStatus();
        return new SidebarStatus
        {
            IsTiming = _timer.IsRunning,
            CurrentUser = _timer.IsRunning ? _timer.CurrentUserName : null,
            IsRemote = remoteStatus.IsRemote,
            RemoteType = remoteStatus.RemoteType,
            Status = remoteStatus.Status,
            ErrorMessage = remoteStatus.ErrorMessage,
            ComputeBusy = compute.IsBusy,
            ComputeSummary = compute.IsBusy
                ? (compute.ProcessCount > 0 ? $"{compute.ProcessCount} 个计算任务" : "CPU 高负载")
                : null,
            Conflict = remoteStatus.Conflict
        };
    }
}
