using Monitor.App.Models;
using Monitor.App.Repositories;

namespace Monitor.App.Services;

public class TimerService
{
    private readonly IUsageRepository _usageRepo;
    private readonly IAuditRepository _auditRepo;

    private bool _running;
    private string _userName = "";
    private DateTime _startTimestamp;
    private long _startCounter; // Stopwatch.GetTimestamp()

    public bool IsRunning => _running;
    public string CurrentUserName => _running ? _userName : "";

    public TimerService(IUsageRepository usageRepo, IAuditRepository auditRepo)
    {
        _usageRepo = usageRepo;
        _auditRepo = auditRepo;
    }

    public bool StartTimer(string userName)
    {
        if (string.IsNullOrWhiteSpace(userName)) return false;
        _userName = userName.Trim();
        _startTimestamp = DateTime.Now;
        _startCounter = System.Diagnostics.Stopwatch.GetTimestamp();
        _running = true;
        _auditRepo.LogAction("timer_start", $"user={_userName}");
        return true;
    }

    public TimerStopResult? StopTimer()
    {
        if (!_running) return null;
        _running = false;

        var endTime = DateTime.Now;
        var elapsed = (long)((System.Diagnostics.Stopwatch.GetTimestamp() - _startCounter)
            / (double)System.Diagnostics.Stopwatch.Frequency);
        var durationSeconds = (int)elapsed;
        var userName = _userName;

        _usageRepo.AddUsageRecord(userName,
            _startTimestamp.ToString("yyyy-MM-dd HH:mm:ss"),
            endTime.ToString("yyyy-MM-dd HH:mm:ss"));

        _auditRepo.LogAction("timer_stop", $"user={userName},duration={durationSeconds}s");

        return new TimerStopResult
        {
            Success = true,
            UserName = userName,
            DurationSeconds = durationSeconds,
            DurationFormatted = FormatDuration(durationSeconds),
            ElapsedFormatted = FormatDuration(durationSeconds)
        };
    }

    public TimerState GetState()
    {
        if (!_running)
            return new TimerState();

        var elapsed = (int)((System.Diagnostics.Stopwatch.GetTimestamp() - _startCounter)
            / (double)System.Diagnostics.Stopwatch.Frequency);

        return new TimerState
        {
            IsRunning = true,
            CurrentUser = _userName,
            StartTime = _startTimestamp.ToString("yyyy-MM-dd HH:mm:ss"),
            ElapsedSeconds = elapsed,
            ElapsedFormatted = FormatDuration(elapsed)
        };
    }

    public List<UseHistoryItem> GetHistory(string filterMode = "all", string search = "")
    {
        var records = _usageRepo.GetUsageRecords(filterMode);
        if (!string.IsNullOrWhiteSpace(search))
            records = records.Where(r => r.UserName.Contains(search, StringComparison.OrdinalIgnoreCase)).ToList();
        return records;
    }

    public void DeleteRecord(int id)
    {
        _usageRepo.DeleteUsageRecord(id);
        _auditRepo.LogAction("record_deleted", $"id={id}");
    }

    public int DeleteRecords(List<int> ids)
    {
        _usageRepo.DeleteUsageRecords(ids);
        _auditRepo.LogAction("records_deleted", $"count={ids.Count}");
        return ids.Count;
    }

    public static string FormatDuration(int seconds)
    {
        var h = seconds / 3600;
        var m = (seconds % 3600) / 60;
        var s = seconds % 60;
        return $"{h:D2}:{m:D2}:{s:D2}";
    }
}

public class TimerStopResult
{
    public bool Success { get; set; }
    public string UserName { get; set; } = "";
    public int DurationSeconds { get; set; }
    public string DurationFormatted { get; set; } = "";
    public string ElapsedFormatted { get; set; } = "";
}
