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

    private DetectionResult? _lastDetection;
    private bool _detectorHealthy = true;
    private bool _detectionDisabled = false;
    private bool _hasSuccessfulDetection = false;
    private string? _lastError;

    // Phase 3: 2 consecutive misses before ending session
    private int _consecutiveMisses = 0;
    private DetectionResult? _lastPositiveDetection;
    private string? _lastOperatorName;

    public RemoteMonitorService(AppSettings settings, IRemoteSessionRepository repo)
    {
        _settings = settings;
        _repo = repo;
        _detector = new ProcessDetector();
    }

    public Task StartAsync(CancellationToken ct)
    {
        // Phase 4C: always clean up stale sessions first, even if detection is disabled
        if (!CleanupStaleSessions())
        {
            Log.Error("RemoteMonitorService startup aborted: stale session cleanup failed");
            _detectorHealthy = false;
            _lastError = "远程会话启动清理失败";
            return Task.CompletedTask;
        }

        if (!_settings.RemoteMonitorEnabled)
        {
            Log.Information("RemoteMonitorService not started (disabled in config)");
            _detectionDisabled = true;
            return Task.CompletedTask;
        }

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

    private bool CleanupStaleSessions()
    {
        try
        {
            var active = _repo.GetActiveRemoteSessions();
            if (active.Count > 0)
            {
                Log.Information("Cleaning up {Count} stale active remote session(s) from previous run",
                    active.Count);
                _repo.EndAllActiveRemoteSessions("app_restarted");
            }

            lock (_lock)
            {
                _remoteType = null;
                _activeSessionId = null;
                _lastPositiveDetection = null;
                _lastOperatorName = null;
                _consecutiveMisses = 0;
            }

            return true;
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to clean up stale active remote sessions");
            return false;
        }
    }

    private void CheckAndUpdate()
    {
        DetectionResult result;
        try
        {
            result = _detector.Detect();
            _detectorHealthy = true;
            _lastError = null;
        }
        catch (Exception ex)
        {
            Log.Error(ex, "RemoteMonitorService detection failed");
            _detectorHealthy = false;
            _lastError = $"Detection error: {ex.Message}";
            return;
        }

        lock (_lock)
        {
            _lastDetection = result;

            if (result.ErrorMessage != null)
            {
                _detectorHealthy = false;
                _lastError = result.ErrorMessage;
                return;
            }

            _detectorHealthy = true;
            _hasSuccessfulDetection = true;
            _lastError = null;

            // Phase 3: only start session for real remote occupancy (IsDetected=true)
            if (result.IsDetected)
            {
                _consecutiveMisses = 0;
                _lastPositiveDetection = result;

                if (_remoteType == null)
                {
                    // New remote session started
                    _remoteType = result.RemoteType;
                    _remoteStartTime = DateTime.Now;
                    _activeSessionId = _repo.AddRemoteSession(
                        remoteType: result.RemoteType ?? "unknown",
                        source: result.Source,
                        operatorName: null);
                    Log.Information(
                        "Remote session started: {Type} confidence={Confidence} signals=[{Signals}]",
                        result.RemoteType, result.Confidence,
                        string.Join(",", result.MatchedSignals));
                }
                else
                {
                    // Same tool still detected — refresh last_seen_at
                    if (_activeSessionId.HasValue)
                        _repo.TouchRemoteSession(_activeSessionId.Value);
                }
            }
            else
            {
                // No strong signal detected
                if (_remoteType != null)
                {
                    _consecutiveMisses++;
                    Log.Debug("Remote signal missed ({Count}/2)", _consecutiveMisses);

                    if (_consecutiveMisses >= 2)
                    {
                        if (_activeSessionId.HasValue)
                            _repo.EndRemoteSession(_activeSessionId.Value, endReason: "normal");
                        Log.Information("Remote session ended: {Type} (after 2 misses)", _remoteType);
                        _remoteType = null;
                        _activeSessionId = null;
                        _consecutiveMisses = 0;
                        _lastPositiveDetection = null;
                        _lastOperatorName = null;
                    }
                }
                else
                {
                    _consecutiveMisses = 0;
                    _lastPositiveDetection = null;
                }
            }
        }
    }

    public RemoteControlStatus GetStatus()
    {
        if (!_detectorHealthy)
        {
            return new RemoteControlStatus
            {
                IsRemote = false, Status = "error",
                ErrorMessage = _lastError ?? "检测服务异常"
            };
        }

        if (_detectionDisabled)
        {
            return new RemoteControlStatus
            {
                IsRemote = false, Status = "unknown",
                ErrorMessage = "远程检测已关闭"
            };
        }

        if (!_hasSuccessfulDetection)
        {
            return new RemoteControlStatus
            {
                IsRemote = false, Status = "unknown",
                ErrorMessage = "远程检测尚未完成首次扫描"
            };
        }

        lock (_lock)
        {
            if (_remoteType == null)
            {
                return new RemoteControlStatus
                {
                    IsRemote = false,
                    Status = "idle",
                    LastSeenAt = _lastDetection?.CheckedAt,
                    Confidence = _lastDetection?.Confidence ?? "",
                    Message = _lastDetection?.Message,
                    MatchedSignals = _lastDetection?.MatchedSignals ?? new()
                };
            }

            // Still tracking a session — use _lastPositiveDetection if in miss countdown
            var positive = _lastPositiveDetection;
            var elapsed = (int)(DateTime.Now - _remoteStartTime).TotalSeconds;
            bool inMissCountdown = _consecutiveMisses > 0 && _consecutiveMisses < 2;

            return new RemoteControlStatus
            {
                IsRemote = true,
                RemoteType = _remoteType,
                Status = "occupied",
                StartTime = _remoteStartTime.ToString("yyyy-MM-dd HH:mm:ss"),
                ElapsedSeconds = elapsed,
                ElapsedFormatted = TimerService.FormatDuration(elapsed),
                OperatorName = _lastOperatorName,
                Source = positive?.Source ?? "process",
                Confidence = positive?.Confidence ?? "low",
                LastSeenAt = positive?.CheckedAt ?? _lastDetection?.CheckedAt,
                Message = inMissCountdown
                    ? "远程信号暂失，等待确认断开"
                    : (positive?.Message ?? _lastDetection?.Message),
                MatchedSignals = positive?.MatchedSignals
                    ?? _lastDetection?.MatchedSignals
                    ?? new()
            };
        }
    }

    public bool TrySetOperatorName(string operatorName, out string error)
    {
        lock (_lock)
        {
            if (_remoteType == null || _activeSessionId == null)
            {
                error = "当前没有活跃的远程占用会话";
                return false;
            }

            var trimmed = operatorName.Trim();
            if (trimmed.Length < 2 || trimmed.Length > 30)
            {
                error = "操作人姓名长度 2-30 个字符";
                return false;
            }

            _repo.UpdateOperatorName(_activeSessionId.Value, trimmed);
            _lastOperatorName = trimmed;
            error = "";
            return true;
        }
    }

    public int? GetActiveSessionId()
    {
        lock (_lock) return _activeSessionId;
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

    // Phase 2: new fields
    public string Status { get; set; } = "unknown"; // idle, occupied, unknown, error
    public string Source { get; set; } = "";
    public string Confidence { get; set; } = "";
    public string? OperatorName { get; set; }
    public string? LastSeenAt { get; set; }
    public string? ErrorMessage { get; set; }
    // Phase 3
    public List<string> MatchedSignals { get; set; } = new();
    public string? Message { get; set; }
}
