using System.Collections.Concurrent;
using Monitor.App.Infrastructure.Config;

namespace Monitor.App.Services;

public class WebAccessService
{
    private readonly AppSettings _settings;
    private readonly ConcurrentDictionary<string, DateTime> _tokens = new();

    public WebAccessService(AppSettings settings) => _settings = settings;

    public string? Authenticate(string password)
    {
        var storedPassword = _settings.WebServerPassword;
        if (password == storedPassword)
        {
            var token = Guid.NewGuid().ToString();
            _tokens[token] = DateTime.Now;
            return token;
        }
        return null;
    }

    public bool ValidateToken(string token) => _tokens.ContainsKey(token);

    public void RevokeToken(string token) => _tokens.TryRemove(token, out _);
}
