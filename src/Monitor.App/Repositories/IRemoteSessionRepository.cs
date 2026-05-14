using Monitor.App.Models;

namespace Monitor.App.Repositories;

public interface IRemoteSessionRepository
{
    int AddRemoteSession(string remoteType, string source = "process", string? operatorName = null);
    void EndRemoteSession(int id, string endReason = "normal");
    void TouchRemoteSession(int id);
    void UpdateOperatorName(int id, string operatorName);
    RemoteSession? GetActiveRemoteSession();
    List<RemoteSession> GetActiveRemoteSessions();
    void EndAllActiveRemoteSessions(string endReason);
    List<RemoteSession> GetRecentRemoteSessions(int limit = 20);
}
