using System.Diagnostics;
using System.Runtime.InteropServices;
using Monitor.App.Infrastructure.Config;
using Monitor.App.Models;

namespace Monitor.App.Services;

/// <summary>
/// 计算任务监控：识别正在运行的重任务进程（Gurobi / Python / MATLAB 等求解程序），
/// 并结合整机 CPU、内存占用判断"是否正在计算"。
///
/// 判定：命中白名单的进程存在 → busy；否则若整机 CPU 使用率 ≥ 阈值（默认 70%）→ busy；
/// 其余 → idle。首次采样完成前为 unknown。
/// </summary>
public class ComputeMonitorService : IDisposable
{
    private readonly AppSettings _settings;
    private readonly object _lock = new();
    private readonly object _sampleLock = new();
    private readonly int _processorCount = Environment.ProcessorCount;

    private CancellationTokenSource? _cts;
    private Task? _task;
    private bool _disposed;

    private ComputeInfo _status = new()
    {
        Status = "unknown",
        Message = "计算监控尚未完成首次采样"
    };

    // CPU 采样差值
    private ulong _prevIdle, _prevKernel, _prevUser;
    private bool _hasPrevCpu;

    // 每进程 CPU 时间差（pid -> TotalProcessorTime ticks）
    private Dictionary<int, long> _prevProcessTicks = new();
    private DateTime _prevSampleTime;

    public ComputeMonitorService(AppSettings settings)
    {
        _settings = settings;
    }

    public void StartAsync(CancellationToken token = default)
    {
        if (_task != null) return;
        _cts = CancellationTokenSource.CreateLinkedTokenSource(token);
        _task = Task.Run(() => RunLoopAsync(_cts.Token));
    }

    public async Task StopAsync(CancellationToken token = default)
    {
        if (_cts == null) return;
        try
        {
            _cts.Cancel();
            if (_task != null)
                await Task.WhenAny(_task, Task.Delay(2000, token));
        }
        catch { /* ignore */ }
    }

    private async Task RunLoopAsync(CancellationToken token)
    {
        var interval = TimeSpan.FromSeconds(Math.Max(1, _settings.ComputeMonitorInterval));
        using var timer = new PeriodicTimer(interval);
        try
        {
            do
            {
                try { Sample(); }
                catch (Exception ex) { SetError(ex.Message); }
            }
            while (await timer.WaitForNextTickAsync(token));
        }
        catch (OperationCanceledException) { }
    }

    /// <summary>执行一次采样，更新状态。可被关机保护等同步调用。</summary>
    public ComputeInfo Sample()
    {
        lock (_sampleLock)
        {
            return SampleCore();
        }
    }

    private ComputeInfo SampleCore()
    {
        if (!_settings.ComputeMonitorEnabled)
        {
            var off = new ComputeInfo
            {
                Status = "idle",
                IsBusy = false,
                Message = "计算监控已在设置中关闭",
                CheckedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };
            lock (_lock) { _status = off; }
            return off;
        }

        var now = DateTime.Now;

        // ---- 整机 CPU ----
        double cpuPercent = 0;
        if (GetSystemTimes(out var idle, out var kernel, out var user))
        {
            var idleTicks = ToUInt64(idle);
            var kernelTicks = ToUInt64(kernel);
            var userTicks = ToUInt64(user);

            if (_hasPrevCpu)
            {
                var dIdle = idleTicks - _prevIdle;
                var dKernel = kernelTicks - _prevKernel;
                var dUser = userTicks - _prevUser;
                var dTotal = dKernel + dUser; // kernel 已包含 idle
                if (dTotal > 0)
                    cpuPercent = Math.Max(0, Math.Min(100, (dTotal - (double)dIdle) / dTotal * 100));
            }
            _prevIdle = idleTicks; _prevKernel = kernelTicks; _prevUser = userTicks;
            _hasPrevCpu = true;
        }

        // ---- 内存 ----
        double memPercent = 0, totalMb = 0, usedMb = 0;
        var mem = new MEMORYSTATUSEX { dwLength = (uint)Marshal.SizeOf<MEMORYSTATUSEX>() };
        if (GlobalMemoryStatusEx(ref mem))
        {
            memPercent = mem.dwMemoryLoad;
            totalMb = mem.ullTotalPhys / 1024.0 / 1024.0;
            usedMb = (mem.ullTotalPhys - mem.ullAvailPhys) / 1024.0 / 1024.0;
        }

        // ---- 重任务进程 ----
        var whitelist = new HashSet<string>(_settings.ComputeJobProcesses ?? new List<string>(), StringComparer.OrdinalIgnoreCase);
        var jobs = new List<JobProcessInfo>();
        var currentTicks = new Dictionary<int, long>();
        var wallSeconds = _prevSampleTime == default ? 0 : (now - _prevSampleTime).TotalSeconds;

        foreach (var p in Process.GetProcesses())
        {
            try
            {
                var name = p.ProcessName;
                if (!whitelist.Contains(name)) continue;

                long ticks = 0;
                try { ticks = p.TotalProcessorTime.Ticks; } catch { }

                double procCpu = 0;
                if (wallSeconds > 0 && _prevProcessTicks.TryGetValue(p.Id, out var prevTicks) && ticks >= prevTicks)
                {
                    var deltaSeconds = (ticks - prevTicks) / (double)TimeSpan.TicksPerSecond;
                    procCpu = Math.Min(100, deltaSeconds / (wallSeconds * _processorCount) * 100);
                }

                double workingSetMb = 0;
                try { workingSetMb = p.WorkingSet64 / 1024.0 / 1024.0; } catch { }

                string? startStr = null;
                int elapsed = 0;
                string elapsedFmt = "00:00:00";
                DateTime? startTime = null;
                try { startTime = p.StartTime; } catch { }
                if (startTime.HasValue)
                {
                    startStr = startTime.Value.ToString("yyyy-MM-dd HH:mm:ss");
                    var span = now - startTime.Value;
                    if (span.TotalSeconds >= 0)
                    {
                        elapsed = (int)span.TotalSeconds;
                        elapsedFmt = span.ToString(@"hh\:mm\:ss");
                    }
                }

                jobs.Add(new JobProcessInfo
                {
                    Pid = p.Id,
                    Name = name,
                    CpuPercent = Math.Round(procCpu, 1),
                    WorkingSetMb = Math.Round(workingSetMb, 1),
                    StartTime = startStr,
                    ElapsedSeconds = elapsed,
                    ElapsedFormatted = elapsedFmt
                });

                currentTicks[p.Id] = ticks;
            }
            catch { /* 进程已退出或无权限，忽略 */ }
            finally { try { p.Dispose(); } catch { } }
        }

        _prevProcessTicks = currentTicks;
        _prevSampleTime = now;

        jobs = jobs.OrderByDescending(j => j.CpuPercent).ThenByDescending(j => j.WorkingSetMb).ToList();

        var threshold = _settings.ComputeCpuThresholdPercent;
        bool busyByCpu = threshold > 0 && cpuPercent >= threshold;
        bool busy = jobs.Count > 0 || busyByCpu;

        string message;
        if (jobs.Count > 0)
            message = $"检测到 {jobs.Count} 个计算任务进程";
        else if (busyByCpu)
            message = $"整机 CPU 负载较高（{cpuPercent:F0}%），可能在计算";
        else
            message = "未检测到计算任务";

        var info = new ComputeInfo
        {
            Status = busy ? "busy" : "idle",
            IsBusy = busy,
            CpuUsagePercent = Math.Round(cpuPercent, 1),
            MemoryUsagePercent = Math.Round(memPercent, 1),
            TotalMemoryUsedMb = Math.Round(usedMb, 0),
            TotalMemoryMb = Math.Round(totalMb, 0),
            ProcessCount = jobs.Count,
            Processes = jobs,
            Message = message,
            CheckedAt = now.ToString("yyyy-MM-dd HH:mm:ss"),
            ErrorMessage = null
        };

        lock (_lock) { _status = info; }
        return info;
    }

    public ComputeInfo GetStatus()
    {
        lock (_lock)
        {
            return new ComputeInfo
            {
                Status = _status.Status,
                IsBusy = _status.IsBusy,
                CpuUsagePercent = _status.CpuUsagePercent,
                MemoryUsagePercent = _status.MemoryUsagePercent,
                TotalMemoryUsedMb = _status.TotalMemoryUsedMb,
                TotalMemoryMb = _status.TotalMemoryMb,
                ProcessCount = _status.ProcessCount,
                Processes = _status.Processes,
                Message = _status.Message,
                CheckedAt = _status.CheckedAt,
                ErrorMessage = _status.ErrorMessage
            };
        }
    }

    private void SetError(string message)
    {
        lock (_lock)
        {
            _status = new ComputeInfo
            {
                Status = "error",
                IsBusy = false,
                ErrorMessage = message,
                Message = $"计算监控采样失败: {message}",
                CheckedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };
        }
    }

    // ---- P/Invoke ----
    [StructLayout(LayoutKind.Sequential)]
    private struct FILETIME { public uint dwLowDateTime; public uint dwHighDateTime; }

    private static ulong ToUInt64(FILETIME ft) => ((ulong)ft.dwHighDateTime << 32) | ft.dwLowDateTime;

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetSystemTimes(out FILETIME idleTime, out FILETIME kernelTime, out FILETIME userTime);

    [StructLayout(LayoutKind.Sequential)]
    private struct MEMORYSTATUSEX
    {
        public uint dwLength;
        public uint dwMemoryLoad;
        public ulong ullTotalPhys;
        public ulong ullAvailPhys;
        public ulong ullTotalPageFile;
        public ulong ullAvailPageFile;
        public ulong ullTotalVirtual;
        public ulong ullAvailVirtual;
        public ulong ullAvailExtendedVirtual;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GlobalMemoryStatusEx(ref MEMORYSTATUSEX lpBuffer);

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        try { _cts?.Cancel(); } catch { }
        try { _cts?.Dispose(); } catch { }
    }
}
