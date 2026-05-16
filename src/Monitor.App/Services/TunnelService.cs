using System.Diagnostics;
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
    private string? _error;
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
        Error = _error
    };

    public async Task<TunnelSetupResult> StartCloudflareLoginAsync(CancellationToken ct = default)
    {
        var path = ResolveCloudflaredPath();
        if (path == null)
            return TunnelSetupResult.Fail("没有找到 cloudflared.exe，请先把它放到软件目录或加入 PATH。");

        var result = await RunCloudflaredCommandAsync(path, "tunnel login", TimeSpan.FromMinutes(5), ct);
        return result.Success
            ? TunnelSetupResult.Ok("Cloudflare 授权已完成，可以继续配置固定域名。")
            : TunnelSetupResult.Fail("Cloudflare 授权失败：" + result.Output);
    }

    public async Task<TunnelSetupResult> ConfigureCloudflareNamedTunnelAsync(string hostname, CancellationToken ct = default)
    {
        hostname = hostname.Trim().ToLowerInvariant();
        if (Uri.CheckHostName(hostname) != UriHostNameType.Dns || !hostname.Contains('.'))
            return TunnelSetupResult.Fail("请输入完整子域名，例如 monitor.fanghaiz.top。");

        var path = ResolveCloudflaredPath();
        if (path == null)
            return TunnelSetupResult.Fail("没有找到 cloudflared.exe，请先把它放到软件目录或加入 PATH。");

        var tunnelName = string.IsNullOrWhiteSpace(_settings.CloudflareTunnelName)
            ? "monitor"
            : _settings.CloudflareTunnelName.Trim();

        var tunnelId = await FindTunnelIdAsync(path, tunnelName, ct);
        if (string.IsNullOrWhiteSpace(tunnelId))
        {
            var create = await RunCloudflaredCommandAsync(path, $"tunnel create {tunnelName}", TimeSpan.FromMinutes(2), ct);
            if (!create.Success)
                return TunnelSetupResult.Fail("创建 Cloudflare 隧道失败：" + create.Output);

            tunnelId = ExtractTunnelId(create.Output);
            if (string.IsNullOrWhiteSpace(tunnelId))
                return TunnelSetupResult.Fail("创建成功，但没有读到 tunnel id。请检查 cloudflared 输出。");
        }

        var credentialsFile = GetCredentialsFile(tunnelId);
        if (!File.Exists(credentialsFile))
            return TunnelSetupResult.Fail("本机缺少隧道凭据文件，请先执行 Cloudflare 授权，再重新配置。");

        var route = await RunCloudflaredCommandAsync(path, $"tunnel route dns {tunnelName} {hostname}", TimeSpan.FromMinutes(2), ct);
        if (!route.Success && !LooksLikeExistingRoute(route.Output))
            return TunnelSetupResult.Fail("绑定域名失败：" + route.Output);

        WriteCloudflaredConfig(tunnelId, hostname, credentialsFile);

        _settings.TunnelEnabled = true;
        _settings.TunnelMode = "cloudflared";
        _settings.TunnelCloudflaredPath = path;
        _settings.CloudflareTunnelName = tunnelName;
        _settings.CloudflareTunnelId = tunnelId;
        _settings.CloudflareHostname = hostname;
        _settings.Save();

        await StopAsync(CancellationToken.None);
        _cts = new CancellationTokenSource();
        _ = RunCloudflared(_cts.Token);

        return TunnelSetupResult.Ok("固定域名已配置，正在启动公网发布。", "https://" + hostname);
    }

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
        if (_process is { HasExited: false })
            _process.Kill(entireProcessTree: true);
        _running = false;
        return Task.CompletedTask;
    }

    private async Task RunCloudflared(CancellationToken ct)
    {
        _error = null;
        var path = ResolveCloudflaredPath();
        if (path == null)
        {
            _error = $"cloudflared 未找到: {_settings.TunnelCloudflaredPath}";
            Log.Warning("cloudflared not found at {Path}", _settings.TunnelCloudflaredPath);
            return;
        }

        var hasFixedHostname = !string.IsNullOrWhiteSpace(_settings.CloudflareHostname)
            && !string.IsNullOrWhiteSpace(_settings.CloudflareTunnelName)
            && !string.IsNullOrWhiteSpace(_settings.CloudflareTunnelId);

        var arguments = hasFixedHostname
            ? $"tunnel --config \"{GetConfigFile()}\" run {_settings.CloudflareTunnelName}"
            : $"tunnel --url http://localhost:{_settings.WebServerPort} --no-autoupdate";

        var psi = new ProcessStartInfo
        {
            FileName = path,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        try
        {
            _process = Process.Start(psi)!;
            _running = true;
            if (hasFixedHostname)
                _publicUrl = "https://" + _settings.CloudflareHostname;

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
            _error = $"cloudflared 启动失败: {ex.Message}";
        }
        _running = false;
    }

    private async Task RunNgrok(CancellationToken ct)
    {
        var path = _settings.TunnelNgrokPath;
        if (!File.Exists(path) && OperatingSystem.IsWindows())
            path = FindExecutable("ngrok.exe") ?? path;

        if (!File.Exists(path))
        {
            _error = $"ngrok 未找到: {path}";
            Log.Warning("ngrok not found at {Path}", path);
            return;
        }

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
            _error = $"ngrok 启动失败: {ex.Message}";
        }
        _running = false;
    }

    private string? ResolveCloudflaredPath()
    {
        foreach (var candidate in CandidateExecutablePaths(_settings.TunnelCloudflaredPath, "cloudflared.exe"))
        {
            if (File.Exists(candidate)) return Path.GetFullPath(candidate);
        }
        return FindExecutable("cloudflared.exe");
    }

    private static IEnumerable<string> CandidateExecutablePaths(string configured, string defaultName)
    {
        if (!string.IsNullOrWhiteSpace(configured))
        {
            yield return configured;
            if (!Path.IsPathRooted(configured))
            {
                yield return Path.Combine(AppDomain.CurrentDomain.BaseDirectory, configured);
                yield return Path.Combine(Environment.CurrentDirectory, configured);
            }
        }

        var dir = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);
        while (dir != null)
        {
            yield return Path.Combine(dir.FullName, defaultName);
            dir = dir.Parent;
        }
    }

    private async Task<string?> FindTunnelIdAsync(string path, string tunnelName, CancellationToken ct)
    {
        var result = await RunCloudflaredCommandAsync(path, "tunnel list", TimeSpan.FromMinutes(1), ct);
        if (!result.Success) return null;

        var pattern = @"(?im)^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s+"
            + Regex.Escape(tunnelName) + @"\s+";
        var match = Regex.Match(result.Output, pattern);
        return match.Success ? match.Groups[1].Value : null;
    }

    private static string? ExtractTunnelId(string output)
    {
        var match = Regex.Match(output, @"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", RegexOptions.IgnoreCase);
        return match.Success ? match.Value : null;
    }

    private static bool LooksLikeExistingRoute(string output)
        => output.Contains("already exists", StringComparison.OrdinalIgnoreCase)
           || output.Contains("already configured", StringComparison.OrdinalIgnoreCase)
           || output.Contains("record already", StringComparison.OrdinalIgnoreCase);

    private static string GetCloudflaredDir()
    {
        var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cloudflared");
        Directory.CreateDirectory(dir);
        return dir;
    }

    private static string GetConfigFile() => Path.Combine(GetCloudflaredDir(), "config.yml");

    private static string GetCredentialsFile(string tunnelId) => Path.Combine(GetCloudflaredDir(), tunnelId + ".json");

    private void WriteCloudflaredConfig(string tunnelId, string hostname, string credentialsFile)
    {
        var config = $"""
tunnel: {tunnelId}
credentials-file: {credentialsFile}

ingress:
  - hostname: {hostname}
    service: http://127.0.0.1:{_settings.WebServerPort}
  - service: http_status:404
""";
        File.WriteAllText(GetConfigFile(), config);
    }

    private static async Task<CommandResult> RunCloudflaredCommandAsync(
        string path, string arguments, TimeSpan timeout, CancellationToken ct)
    {
        var psi = new ProcessStartInfo
        {
            FileName = path,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = Process.Start(psi);
        if (process == null)
            return new CommandResult(false, "cloudflared 启动失败");

        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeoutCts.CancelAfter(timeout);

        try
        {
            var stdout = process.StandardOutput.ReadToEndAsync(timeoutCts.Token);
            var stderr = process.StandardError.ReadToEndAsync(timeoutCts.Token);
            await process.WaitForExitAsync(timeoutCts.Token);
            var output = ((await stdout) + "\n" + (await stderr)).Trim();
            return new CommandResult(process.ExitCode == 0, output);
        }
        catch (OperationCanceledException)
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            return new CommandResult(false, "cloudflared 执行超时");
        }
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
            _process.Kill(entireProcessTree: true);
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

public record TunnelSetupResult(bool Success, string Message, string? PublicUrl = null)
{
    public static TunnelSetupResult Ok(string message, string? publicUrl = null) => new(true, message, publicUrl);
    public static TunnelSetupResult Fail(string message) => new(false, message);
}

public record CommandResult(bool Success, string Output);
