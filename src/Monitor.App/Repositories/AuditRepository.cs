using Dapper;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Models;

namespace Monitor.App.Repositories;

public class AuditRepository : IAuditRepository
{
    private readonly DbConnectionFactory _factory;

    public AuditRepository(DbConnectionFactory factory) => _factory = factory;

    public void LogAction(string action, string? details = null)
    {
        using var conn = _factory.CreateConnection();
        conn.Execute("INSERT INTO audit_log (action, details) VALUES (@Action, @Details)",
            new { Action = action, Details = details });
    }

    public List<AuditLog> GetAuditLogs(int limit = 100)
    {
        using var conn = _factory.CreateConnection();
        return conn.Query<AuditLog>(
            "SELECT id AS Id, action AS Action, details AS Details, timestamp AS Timestamp FROM audit_log ORDER BY timestamp DESC LIMIT @Limit",
            new { Limit = limit }).AsList();
    }
}
