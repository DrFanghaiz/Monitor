using System.Collections.Concurrent;
using Monitor.App.Infrastructure.Config;

namespace Monitor.App.Services;

public class WebAccessService
{
    private static readonly TimeSpan TokenLifetime = TimeSpan.FromHours(12);
    private static readonly TimeSpan LockDuration = TimeSpan.FromMinutes(10);
    private static readonly int MaxFailures = 5;
    private static readonly TimeSpan FailWindow = TimeSpan.FromMinutes(10);

    private readonly AppSettings _settings;
    private readonly ConcurrentDictionary<string, DateTime> _tokens = new();
    private readonly ConcurrentDictionary<string, FailState> _loginFailures = new();
    private readonly ConcurrentDictionary<string, FailState> _registrationFailures = new();

    public WebAccessService(AppSettings settings) => _settings = settings;

    public string? Authenticate(string password, string? remoteIp)
    {
        var ip = NormalizeIp(remoteIp);
        if (IsLocked(_loginFailures, ip))
            return null;

        if (password == _settings.WebServerPassword)
        {
            _loginFailures.TryRemove(ip, out _);
            var token = Guid.NewGuid().ToString();
            _tokens[token] = DateTime.UtcNow;
            return token;
        }

        RecordFailure(_loginFailures, ip);
        return null;
    }

    public bool IsLoginLocked(string? remoteIp) => IsLocked(_loginFailures, NormalizeIp(remoteIp));

    public bool ValidateToken(string token)
    {
        var now = DateTime.UtcNow;
        foreach (var kv in _tokens)
        {
            if (now - kv.Value > TokenLifetime)
                _tokens.TryRemove(kv.Key, out _);
        }

        if (!_tokens.TryGetValue(token, out var issued))
            return false;

        if (now - issued > TokenLifetime)
        {
            _tokens.TryRemove(token, out _);
            return false;
        }

        return true;
    }

    public void RevokeToken(string token) => _tokens.TryRemove(token, out _);

    public bool IsRegistrationLocked(string? remoteIp)
        => IsLocked(_registrationFailures, NormalizeIp(remoteIp));

    public void RecordRegistrationFailure(string? remoteIp)
        => RecordFailure(_registrationFailures, NormalizeIp(remoteIp));

    public void ClearRegistrationFailures(string? remoteIp)
        => _registrationFailures.TryRemove(NormalizeIp(remoteIp), out _);

    private static string NormalizeIp(string? remoteIp)
        => string.IsNullOrWhiteSpace(remoteIp) ? "127.0.0.1" : remoteIp;

    private static bool IsLocked(ConcurrentDictionary<string, FailState> source, string ip)
    {
        if (!source.TryGetValue(ip, out var state))
            return false;

        var now = DateTime.UtcNow;
        if (!state.LockedUntilUtc.HasValue)
            return false;

        if (now < state.LockedUntilUtc.Value)
            return true;

        source.TryRemove(ip, out _);
        return false;
    }

    private static void RecordFailure(ConcurrentDictionary<string, FailState> source, string ip)
    {
        var now = DateTime.UtcNow;
        source.AddOrUpdate(ip,
            _ => new FailState { WindowStartUtc = now, FailCount = 1 },
            (_, state) =>
            {
                if (now - state.WindowStartUtc > FailWindow)
                {
                    state.WindowStartUtc = now;
                    state.FailCount = 1;
                    state.LockedUntilUtc = null;
                }
                else
                {
                    state.FailCount++;
                    if (state.FailCount >= MaxFailures)
                        state.LockedUntilUtc = now + LockDuration;
                }

                return state;
            });
    }

    private sealed class FailState
    {
        public DateTime WindowStartUtc;
        public int FailCount;
        public DateTime? LockedUntilUtc;
    }
}
