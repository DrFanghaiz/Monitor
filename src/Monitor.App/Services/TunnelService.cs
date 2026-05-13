using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using Monitor.App.Infrastructure.Config;
using Serilog;

namespace Monitor.App.Services;

public class TunnelService : IDisposable
{
    private readonly AppSettings _settings;
    private Process? _process;
    private string? _publicUrl;
    private bool _running;
    private CancellationTokenSource? _cts;

    public string? PublicUrl => _publicUrl;
    public bool IsRunning => _running;

    public TunnelService(AppSettings settings)
    {
        _settings = settings;
    }

    public string? GetPublicUrl()
    {
        var url = _publicUrl;
        if (url != null && !url.StartsWith("https://"))
            url = "https://" + url;
        return url;
    }

    public TunnelStatus GetStatus() => new()
    {
        Running = _running,
        PublicUrl = _publicUrl,
        Mode = _settings.TunnelMode,
        Error = null
    };

    public Task StartAsync(CancellationToken ct)
    {
        if (!_settings.TunnelEnabled) return Task.CompletedTask;

        Log.Information("TunnelService starting with mode: {Mode}", _settings.TunnelMode);
        _cts = CancellationTokenSource.CreateLinkedTokenSource(ct);

        if (_settings.TunnelMode == "cloudflared")
            _ = RunCloudflared(_cts.Token);
        else
            _ = RunNgrok(_cts.Token);

        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken ct)
    {
        _cts?.Cancel();
        _process?.Kill();
        _running = false;
        return Task.CompletedTask;
    }

    private async Task RunCloudflared(CancellationToken ct)
    {
        var path = _settings.TunnelCloudflaredPath;
        if (!File.Exists(path) && OperatingSystem.IsWindows())
            path = FindExecutable("cloudflared.exe") ?? path;

        var port = _settings.WebServerPort;
        var psi = new ProcessStartInfo
        {
            FileName = path,
            Arguments = $"tunnel --url http://localhost:{port} --no-autoupdate",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        try
        {
            _process = Process.Start(psi)!;
            _running = true;

            var reader = _process.StandardOutput;
            var regex = new Regex(@"https://[a-zA-Z0-9\-]+\.trycloudflare\.com");

            try
            {
                while (!ct.IsCancellationRequested)
                {
                    var line = await reader.ReadLineAsync(ct);
                    if (line == null) break;
                    var match = regex.Match(line);
                    if (match.Success)
                    {
                        _publicUrl = match.Value;
                        Log.Information("Tunnel URL: {Url}", _publicUrl);
                    }
                }
            }
            catch (OperationCanceledException) { }

            await _process.WaitForExitAsync(CancellationToken.None);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to start cloudflared");
        }
        _running = false;
    }

    private async Task RunNgrok(CancellationToken ct)
    {
        var path = _settings.TunnelNgrokPath;
        if (!File.Exists(path) && OperatingSystem.IsWindows())
            path = FindExecutable("ngrok.exe") ?? path;

        var args = $"http {_settings.WebServerPort} --log=stdout --log-format=json";
        if (!string.IsNullOrEmpty(_settings.TunnelNgrokAuthToken))
            args += $" --authtoken {_settings.TunnelNgrokAuthToken}";

        var psi = new ProcessStartInfo
        {
            FileName = path,
            Arguments = args,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        try
        {
            _process = Process.Start(psi)!;
            _running = true;

            var reader = _process.StandardOutput;
            var regex = new Regex(@"""url"":""([^""]+)""");

            try
            {
                while (!ct.IsCancellationRequested)
                {
                    var line = await reader.ReadLineAsync(ct);
                    if (line == null) break;
                    if (line.Contains("\"url\""))
                    {
                        var match = regex.Match(line);
                        if (match.Success)
                        {
                            _publicUrl = match.Groups[1].Value.Replace("tcp://", "");
                            Log.Information("Tunnel URL: {Url}", _publicUrl);
                        }
                    }
                }
            }
            catch (OperationCanceledException) { }

            await _process.WaitForExitAsync(CancellationToken.None);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to start ngrok");
        }
        _running = false;
    }

    private static string? FindExecutable(string name)
    {
        var paths = Environment.GetEnvironmentVariable("PATH")?.Split(Path.PathSeparator) ?? Array.Empty<string>();
        foreach (var dir in paths)
        {
            var full = Path.Combine(dir, name);
            if (File.Exists(full)) return full;
        }
        return null;
    }

    public void Dispose()
    {
        _cts?.Cancel();
        if (_process is { HasExited: false })
            _process.Kill();
        _process?.Dispose();
        _cts?.Dispose();
    }
}

public class TunnelStatus
{
    public bool Running { get; set; }
    public string? PublicUrl { get; set; }
    public string? Mode { get; set; }
    public string? Error { get; set; }
}
