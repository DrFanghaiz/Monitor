using Monitor.App.Models;
using Monitor.App.Repositories;

namespace Monitor.App.Services;

public class StatusService
{
    private readonly TimerService _timer;
    private readonly RemoteMonitorService _remoteMonitor;
    private readonly IUsageRepository _usageRepo;
    private readonly IReservationRepository _reservationRepo;

    public StatusService(TimerService timer, RemoteMonitorService remoteMonitor,
        IUsageRepository usageRepo, IReservationRepository reservationRepo)
    {
        _timer = timer;
        _remoteMonitor = remoteMonitor;
        _usageRepo = usageRepo;
        _reservationRepo = reservationRepo;
    }

    public AppStatus GetFullStatus()
    {
        var timerState = _timer.GetState();
        var remoteStatus = _remoteMonitor.GetStatus();

        string computerStatus;
        if (remoteStatus.Status == "error") computerStatus = "error";
        else if (remoteStatus.Status == "unknown") computerStatus = "unknown";
        else if (remoteStatus.IsRemote) computerStatus = "remote_controlled";
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
                Message = remoteStatus.Message
            },
            TodayRecords = _usageRepo.GetTodayRecords(),
            TodayReservations = _reservationRepo.GetTodayReservations(todayStr)
        };
    }

    public SidebarStatus GetSidebarStatus()
    {
        var remoteStatus = _remoteMonitor.GetStatus();
        return new SidebarStatus
        {
            IsTiming = _timer.IsRunning,
            CurrentUser = _timer.IsRunning ? _timer.CurrentUserName : null,
            IsRemote = remoteStatus.IsRemote,
            RemoteType = remoteStatus.RemoteType,
            Status = remoteStatus.Status,
            ErrorMessage = remoteStatus.ErrorMessage
        };
    }
}
