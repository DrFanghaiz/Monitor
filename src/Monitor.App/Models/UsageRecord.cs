namespace Monitor.App.Models;

public class UsageRecord
{
    public int Id { get; set; }
    public string UserName { get; set; } = "";
    public string StartTime { get; set; } = "";
    public string EndTime { get; set; } = "";
    public int DurationSeconds { get; set; }
    public string CreatedAt { get; set; } = "";
}

public class UseHistoryItem
{
    public int Id { get; set; }
    public string UserName { get; set; } = "";
    public string StartTime { get; set; } = "";
    public string EndTime { get; set; } = "";
    public int DurationSeconds { get; set; }
    public string CreatedAt { get; set; } = "";
}

public class UserStat
{
    public string UserName { get; set; } = "";
    public int TotalSeconds { get; set; }
    public string LastSeen { get; set; } = "";
}

public class HourlyStat
{
    public string Date { get; set; } = "";
    public int Hour { get; set; }
    public double Hours { get; set; }
}

public class DailyStat
{
    public string Date { get; set; } = "";
    public double Hours { get; set; }
    public int Users { get; set; }
}
