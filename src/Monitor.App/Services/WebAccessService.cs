using System.Collections.Concurrent;
using Monitor.App.Infrastructure.Config;

namespace Monitor.App.Services;

public class WebAccessService
{
    private static readonly TimeSpan TokenLifetime = TimeSpan.FromHours(12);
    private static readonly TimeSpan LoginLockDuration = TimeSpan.FromMinutes(10);
    private static readonly int MaxLoginFailures = 5;
    private static readonly TimeSpan LoginFailWindow = TimeSpan.FromMinutes(10);

    private readonly AppSettings _settings;
    private readonly ConcurrentDictionary<string, DateTime> _tokens = new();
    private readonly ConcurrentDictionary<string, LoginFailState> _failures = new();

    public WebAccessService(AppSettings settings) => _settings = settings;

    public string? Authenticate(string password, string? remoteIp)
    {
        var ip = remoteIp ?? "127.0.0.1";

        // Check if this IP is locked
        if (IsLoginLocked(ip))
            return null;

        var storedPassword = _settings.WebServerPassword;
        if (password == storedPassword)
        {
            // Success — clear failures, generate token
            _failures.TryRemove(ip, out _);
            var token = Guid.NewGuid().ToString();
            _tokens[token] = DateTime.UtcNow;
            return token;
        }

        // Failure — increment counter with proper window tracking
        RecordLoginFailure(ip);
        return null;
    }

    public bool IsLoginLocked(string? remoteIp)
    {
        var ip = remoteIp ?? "127.0.0.1";
        if (!_failures.TryGetValue(ip, out var state))
            return false;

        var now = DateTime.UtcNow;

        // If locked and lock hasn't expired → still locked
        if (state.LockedUntilUtc.HasValue)
        {
            if (now < state.LockedUntilUtc.Value)
                return true;
            // Lock expired → remove record
            _failures.TryRemove(ip, out _);
            return false;
        }

        return false;
    }

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

    private void RecordLoginFailure(string ip)
    {
        var now = DateTime.UtcNow;

        _failures.AddOrUpdate(ip,
            _ => new LoginFailState { WindowStartUtc = now, FailCount = 1 },
            (_, s) =>
            {
                // If failure window expired → reset
                if (now - s.WindowStartUtc > LoginFailWindow)
                {
                    s.WindowStartUtc = now;
                    s.FailCount = 1;
                    s.LockedUntilUtc = null;
                }
                else
                {
                    s.FailCount++;
                    if (s.FailCount >= MaxLoginFailures)
                        s.LockedUntilUtc = now + LoginLockDuration;
                }
                return s;
            });
    }

    private class LoginFailState
    {
        public DateTime WindowStartUtc;
        public int FailCount;
        public DateTime? LockedUntilUtc;
    }
}
