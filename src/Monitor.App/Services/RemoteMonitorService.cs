using Monitor.App.Infrastructure.Config;
using Monitor.App.Infrastructure.System;
using Monitor.App.Repositories;
using Serilog;

namespace Monitor.App.Services;

public class RemoteMonitorService : IDisposable
{
    private readonly ProcessDetector _detector;
    private readonly IRemoteSessionRepository _repo;
    private readonly AppSettings _settings;
    private Timer? _timer;

    private string? _remoteType;
    private DateTime _remoteStartTime;
    private int? _activeSessionId;
    private readonly object _lock = new();

    public RemoteMonitorService(AppSettings settings, IRemoteSessionRepository repo)
    {
        _settings = settings;
        _repo = repo;
        _detector = new ProcessDetector(settings.RemoteTools);
    }

    public Task StartAsync(CancellationToken ct)
    {
        if (!_settings.RemoteMonitorEnabled) return Task.CompletedTask;

        Log.Information("RemoteMonitorService started");
        var interval = TimeSpan.FromSeconds(_settings.RemoteMonitorInterval);
        _timer = new Timer(_ =>
        {
            CheckAndUpdate();
        }, null, TimeSpan.Zero, interval);
        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken ct)
    {
        _timer?.Dispose();
        _timer = null;
        return Task.CompletedTask;
    }

    private void CheckAndUpdate()
    {
        lock (_lock)
        {
            var detected = _detector.Detect();

            if (detected != null && _remoteType == null)
            {
                _remoteType = detected;
                _remoteStartTime = DateTime.Now;
                _activeSessionId = _repo.AddRemoteSession(detected);
                Log.Information("Remote session started: {Type}", detected);
            }
            else if (detected == null && _remoteType != null)
            {
                if (_activeSessionId.HasValue)
                    _repo.EndRemoteSession(_activeSessionId.Value);
                Log.Information("Remote session ended: {Type}", _remoteType);
                _remoteType = null;
                _activeSessionId = null;
            }
        }
    }

    public RemoteControlStatus GetStatus()
    {
        lock (_lock)
        {
            if (_remoteType == null)
                return new RemoteControlStatus();

            var elapsed = (int)(DateTime.Now - _remoteStartTime).TotalSeconds;
            return new RemoteControlStatus
            {
                IsRemote = true,
                RemoteType = _remoteType,
                StartTime = _remoteStartTime.ToString("yyyy-MM-dd HH:mm:ss"),
                ElapsedSeconds = elapsed,
                ElapsedFormatted = TimerService.FormatDuration(elapsed)
            };
        }
    }

    public void Dispose()
    {
        _timer?.Dispose();
    }
}

public class RemoteControlStatus
{
    public bool IsRemote { get; set; }
    public string? RemoteType { get; set; }
    public string? StartTime { get; set; }
    public int ElapsedSeconds { get; set; }
    public string ElapsedFormatted { get; set; } = "00:00:00";
}
