namespace Monitor.App.Models;

public class AppStatus
{
    public string Timestamp { get; set; } = "";
    /// <summary>
    /// idle, in_use, remote_controlled, computing, unknown, error
    /// 失败即安全：检测状态未知/未就绪时按 remote_controlled 保守处理。
    /// </summary>
    public string ComputerStatus { get; set; } = "idle";

    public LocalUseInfo LocalUse { get; set; } = new();
    public RemoteControlInfo RemoteControl { get; set; } = new();
    public ComputeInfo Compute { get; set; } = new();
    public List<UseHistoryItem> TodayRecords { get; set; } = new();
    public List<Reservation> TodayReservations { get; set; } = new();
}

public class LocalUseInfo
{
    public string? CurrentUser { get; set; }
    public string? StartTime { get; set; }
    public int ElapsedSeconds { get; set; }
    public string ElapsedFormatted { get; set; } = "00:00:00";
}

public class RemoteControlInfo
{
    public bool IsRemote { get; set; }
    public string? RemoteType { get; set; }
    public string? StartTime { get; set; }
    public int ElapsedSeconds { get; set; }
    public string ElapsedFormatted { get; set; } = "00:00:00";

    // Phase 2
    public string Status { get; set; } = "unknown"; // idle, occupied, unknown, initializing, disabled, error
    public string Source { get; set; } = "";
    public string Confidence { get; set; } = "";
    public string? OperatorName { get; set; }
    public string? LastSeenAt { get; set; }
    public string? ErrorMessage { get; set; }
    // Phase 3
    public List<string> MatchedSignals { get; set; } = new();
    public string? Message { get; set; }
    /// <summary>仅后台运行、未确认会话的远控工具显示名。</summary>
    public List<string> RunningTools { get; set; } = new();

    // Phase 5: 并发冲突
    /// <summary>当前同时处于"会话"状态的远控工具数量。</summary>
    public int ActiveToolCount { get; set; }
    /// <summary>是否检测到多个远控工具同时在线（可能多人同时控制）。</summary>
    public bool Conflict { get; set; }
}

/// <summary>计算任务监控状态（重任务进程 + 整机 CPU/内存）。</summary>
public class ComputeInfo
{
    /// <summary>idle, busy, unknown, error</summary>
    public string Status { get; set; } = "unknown";
    public bool IsBusy { get; set; }
    public double CpuUsagePercent { get; set; }
    public double MemoryUsagePercent { get; set; }
    public double TotalMemoryUsedMb { get; set; }
    public double TotalMemoryMb { get; set; }
    public int ProcessCount { get; set; }
    public List<JobProcessInfo> Processes { get; set; } = new();
    public string? Message { get; set; }
    public string? CheckedAt { get; set; }
    public string? ErrorMessage { get; set; }
}

/// <summary>单个重任务进程。</summary>
public class JobProcessInfo
{
    public int Pid { get; set; }
    public string Name { get; set; } = "";
    public double CpuPercent { get; set; }
    public double WorkingSetMb { get; set; }
    public string? StartTime { get; set; }
    public int ElapsedSeconds { get; set; }
    public string ElapsedFormatted { get; set; } = "00:00:00";
}

public class TimerState
{
    public bool IsRunning { get; set; }
    public string? CurrentUser { get; set; }
    public string? StartTime { get; set; }
    public int ElapsedSeconds { get; set; }
    public string ElapsedFormatted { get; set; } = "00:00:00";
}

public class SidebarStatus
{
    public bool IsTiming { get; set; }
    public string? CurrentUser { get; set; }
    public bool IsRemote { get; set; }
    public string? RemoteType { get; set; }
    public string Status { get; set; } = "unknown";
    public string? ErrorMessage { get; set; }

    // 计算任务
    public bool ComputeBusy { get; set; }
    public string? ComputeSummary { get; set; }

    // 并发冲突
    public bool Conflict { get; set; }
}
