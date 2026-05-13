using Monitor.App.Models;

namespace Monitor.App.Repositories;

public interface IAuditRepository
{
    void LogAction(string action, string? details = null);
    List<AuditLog> GetAuditLogs(int limit = 100);
}
