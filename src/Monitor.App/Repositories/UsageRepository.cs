using Dapper;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Models;

namespace Monitor.App.Repositories;

public class UsageRepository : IUsageRepository
{
    private readonly DbConnectionFactory _factory;

    public UsageRepository(DbConnectionFactory factory) => _factory = factory;

    public int AddUsageRecord(string userName, string startTime, string endTime)
    {
        using var conn = _factory.CreateConnection();
        var start = DateTime.Parse(startTime);
        var end = DateTime.Parse(endTime);
        var duration = (int)(end - start).TotalSeconds;

        var sql = "INSERT INTO usage_records (user_name, start_time, end_time, duration_seconds) VALUES (@Name, @Start, @End, @Duration); SELECT last_insert_rowid();";
        return conn.ExecuteScalar<int>(sql, new { Name = userName, Start = startTime, End = endTime, Duration = duration });
    }

    public List<UseHistoryItem> GetUsageRecords(string filterMode = "all")
    {
        using var conn = _factory.CreateConnection();
        var sql = "SELECT id, user_name AS UserName, start_time AS StartTime, end_time AS EndTime, duration_seconds AS DurationSeconds, created_at AS CreatedAt FROM usage_records";
        if (filterMode == "today")
            sql += " WHERE date(start_time) = date('now', 'localtime')";
        else if (filterMode == "this month")
            sql += " WHERE strftime('%Y-%m', start_time) = strftime('%Y-%m', 'now', 'localtime')";
        sql += " ORDER BY start_time DESC";
        return conn.Query<UseHistoryItem>(sql).AsList();
    }

    public List<UseHistoryItem> GetTodayRecords() => GetUsageRecords("today");

    public List<UserStat> GetUserStats(string filterMode = "all")
    {
        using var conn = _factory.CreateConnection();
        var sql = "SELECT user_name AS UserName, SUM(duration_seconds) AS TotalSeconds, MAX(end_time) AS LastSeen FROM usage_records";
        if (filterMode == "today")
            sql += " WHERE date(start_time) = date('now', 'localtime')";
        else if (filterMode == "this month")
            sql += " WHERE strftime('%Y-%m', start_time) = strftime('%Y-%m', 'now', 'localtime')";
        sql += " GROUP BY user_name ORDER BY TotalSeconds DESC";
        return conn.Query<UserStat>(sql).AsList();
    }

    public void DeleteUsageRecord(int id)
    {
        using var conn = _factory.CreateConnection();
        conn.Execute("DELETE FROM usage_records WHERE id = @Id", new { Id = id });
    }

    public void DeleteUsageRecords(List<int> ids)
    {
        if (ids.Count == 0) return;
        using var conn = _factory.CreateConnection();
        conn.Execute($"DELETE FROM usage_records WHERE id IN ({string.Join(",", ids)})");
    }

    public List<HourlyStat> GetHourlyStats()
    {
        using var conn = _factory.CreateConnection();
        var sql = @"
            SELECT date(start_time) AS Date,
                   CAST(strftime('%H', start_time) AS INTEGER) AS Hour,
                   ROUND(SUM(duration_seconds) / 3600.0, 2) AS Hours
            FROM usage_records
            GROUP BY date(start_time), strftime('%H', start_time)
            ORDER BY date(start_time), Hour";
        return conn.Query<HourlyStat>(sql).AsList();
    }

    public List<DailyStat> GetDailyStats(int days = 30)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"
            SELECT date(start_time) AS Date,
                   ROUND(SUM(duration_seconds) / 3600.0, 2) AS Hours,
                   COUNT(DISTINCT user_name) AS Users
            FROM usage_records
            WHERE start_time >= date('now', 'localtime', @Days)
            GROUP BY date(start_time)
            ORDER BY date(start_time)";
        return conn.Query<DailyStat>(sql, new { Days = $"-{days} days" }).AsList();
    }

    public List<UserStat> GetUserDistribution(string filterMode = "all") => GetUserStats(filterMode);
}
