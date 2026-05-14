using Dapper;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Models;

namespace Monitor.App.Repositories;

public class RemoteSessionRepository : IRemoteSessionRepository
{
    private readonly DbConnectionFactory _factory;

    public RemoteSessionRepository(DbConnectionFactory factory) => _factory = factory;

    public int AddRemoteSession(string remoteType, string source = "process", string? operatorName = null)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"INSERT INTO remote_sessions (remote_type, start_time, source, operator_name, last_seen_at)
                    VALUES (@Type, datetime('now', 'localtime'), @Source, @OperatorName, datetime('now', 'localtime'));
                    SELECT last_insert_rowid();";
        return conn.ExecuteScalar<int>(sql, new
        {
            Type = remoteType,
            Source = source,
            OperatorName = (object?)operatorName ?? DBNull.Value
        });
    }

    public void EndRemoteSession(int id, string endReason = "normal")
    {
        using var conn = _factory.CreateConnection();
        var sql = @"UPDATE remote_sessions SET
                    end_time = datetime('now', 'localtime'),
                    duration_seconds = CAST((julianday(datetime('now', 'localtime')) - julianday(start_time)) * 86400 AS INTEGER),
                    is_active = 0,
                    end_reason = @EndReason
                    WHERE id = @Id";
        conn.Execute(sql, new { Id = id, EndReason = endReason });
    }

    public void TouchRemoteSession(int id)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"UPDATE remote_sessions SET
                    last_seen_at = datetime('now', 'localtime')
                    WHERE id = @Id";
        conn.Execute(sql, new { Id = id });
    }

    public void UpdateOperatorName(int id, string operatorName)
    {
        using var conn = _factory.CreateConnection();
        conn.Execute(
            "UPDATE remote_sessions SET operator_name = @Name WHERE id = @Id",
            new { Id = id, Name = operatorName });
    }

    public RemoteSession? GetActiveRemoteSession()
    {
        var sessions = GetActiveRemoteSessions();
        return sessions.FirstOrDefault();
    }

    public List<RemoteSession> GetActiveRemoteSessions()
    {
        using var conn = _factory.CreateConnection();
        return conn.Query<RemoteSession>(
            @"SELECT id AS Id, remote_type AS RemoteType, start_time AS StartTime,
                     end_time AS EndTime, duration_seconds AS DurationSeconds,
                     is_active AS IsActive, created_at AS CreatedAt,
                     operator_name AS OperatorName, source AS Source,
                     end_reason AS EndReason, last_seen_at AS LastSeenAt
              FROM remote_sessions WHERE is_active = 1").AsList();
    }

    public void EndAllActiveRemoteSessions(string endReason)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"UPDATE remote_sessions SET
                    end_time = datetime('now', 'localtime'),
                    duration_seconds = CAST((julianday(datetime('now', 'localtime')) - julianday(start_time)) * 86400 AS INTEGER),
                    is_active = 0,
                    end_reason = @EndReason
                    WHERE is_active = 1";
        conn.Execute(sql, new { EndReason = endReason });
    }

    public List<RemoteSession> GetRecentRemoteSessions(int limit = 20)
    {
        using var conn = _factory.CreateConnection();
        return conn.Query<RemoteSession>(
            @"SELECT id AS Id, remote_type AS RemoteType, start_time AS StartTime,
                     end_time AS EndTime, duration_seconds AS DurationSeconds,
                     is_active AS IsActive, created_at AS CreatedAt,
                     operator_name AS OperatorName, source AS Source,
                     end_reason AS EndReason, last_seen_at AS LastSeenAt
              FROM remote_sessions ORDER BY start_time DESC LIMIT @Limit",
            new { Limit = limit }).AsList();
    }
}
