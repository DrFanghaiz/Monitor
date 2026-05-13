using Dapper;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Models;

namespace Monitor.App.Repositories;

public class RemoteSessionRepository : IRemoteSessionRepository
{
    private readonly DbConnectionFactory _factory;

    public RemoteSessionRepository(DbConnectionFactory factory) => _factory = factory;

    public int AddRemoteSession(string remoteType)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"INSERT INTO remote_sessions (remote_type, start_time)
                    VALUES (@Type, datetime('now', 'localtime')); SELECT last_insert_rowid();";
        return conn.ExecuteScalar<int>(sql, new { Type = remoteType });
    }

    public void EndRemoteSession(int id)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"UPDATE remote_sessions SET
                    end_time = datetime('now', 'localtime'),
                    duration_seconds = CAST((julianday('now') - julianday(start_time)) * 86400 AS INTEGER),
                    is_active = 0
                    WHERE id = @Id";
        conn.Execute(sql, new { Id = id });
    }

    public RemoteSession? GetActiveRemoteSession()
    {
        using var conn = _factory.CreateConnection();
        return conn.QueryFirstOrDefault<RemoteSession>(
            "SELECT id AS Id, remote_type AS RemoteType, start_time AS StartTime, end_time AS EndTime, duration_seconds AS DurationSeconds, is_active AS IsActive, created_at AS CreatedAt FROM remote_sessions WHERE is_active = 1 LIMIT 1");
    }

    public List<RemoteSession> GetRecentRemoteSessions(int limit = 20)
    {
        using var conn = _factory.CreateConnection();
        return conn.Query<RemoteSession>(
            "SELECT id AS Id, remote_type AS RemoteType, start_time AS StartTime, end_time AS EndTime, duration_seconds AS DurationSeconds, is_active AS IsActive, created_at AS CreatedAt FROM remote_sessions ORDER BY start_time DESC LIMIT @Limit",
            new { Limit = limit }).AsList();
    }
}
