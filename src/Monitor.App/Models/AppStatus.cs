namespace Monitor.App.Models;

public class AppStatus
{
    public string Timestamp { get; set; } = "";
    public string ComputerStatus { get; set; } = "idle"; // idle, in_use, remote_controlled

    public LocalUseInfo LocalUse { get; set; } = new();
    public RemoteControlInfo RemoteControl { get; set; } = new();
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
}
