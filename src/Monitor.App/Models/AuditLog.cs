namespace Monitor.App.Models;

public class AuditLog
{
    public int Id { get; set; }
    public string Action { get; set; } = "";
    public string? Details { get; set; }
    public string Timestamp { get; set; } = "";
}
