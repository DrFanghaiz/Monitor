namespace Monitor.App.Models;

public class RemoteSession
{
    public int Id { get; set; }
    public string RemoteType { get; set; } = "";
    public string StartTime { get; set; } = "";
    public string? EndTime { get; set; }
    public int DurationSeconds { get; set; }
    public bool IsActive { get; set; }
    public string CreatedAt { get; set; } = "";

    // Phase 2: new fields
    public string? OperatorName { get; set; }
    public string Source { get; set; } = "process";
    public string? EndReason { get; set; }
    public string? LastSeenAt { get; set; }
}
