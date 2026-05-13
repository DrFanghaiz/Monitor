using Monitor.App.Models;

namespace Monitor.App.Repositories;

public interface IRemoteSessionRepository
{
    int AddRemoteSession(string remoteType);
    void EndRemoteSession(int id);
    RemoteSession? GetActiveRemoteSession();
    List<RemoteSession> GetRecentRemoteSessions(int limit = 20);
}
