using System.Diagnostics;
using System.Net;
using System.Net.NetworkInformation;
using System.Runtime.InteropServices;
using System.Text;

namespace Monitor.App.Infrastructure.System;

/// <summary>
/// Phase 3: Sunlogin (向日葵) strong detection only.
/// Scans ALL running processes for AweSun.exe variants.
/// Other remote tools (TeamViewer, AnyDesk, ToDesk) are ignored for now.
/// </summary>
public class ProcessDetector
{
    // AweSun executable name to scan for (case-insensitive match)
    private const string AweSunExe = "AweSun.exe";
    private const string AweSunGuardExe = "awesun_guard.exe";
    private const string AweSunServiceExe = "AweSunService.exe";

    // Agent sub-path (case-insensitive contains match)
    private const string SunloginAgentPath = @"\SunloginClient\agent\";
    private const string SunloginClientPath = @"\SunloginClient\";

    // Session window title (exact match)
    private const string SessionWindowTitle = "向日葵-远程会话";

    public ProcessDetector() { }

    public DetectionResult Detect()
    {
        try
        {
            var signals = new List<string>();
            bool hasAgent = false;
            bool hasSessionWindow = false;
            bool hasBackground = false;

            // ---- Scan ALL processes for AweSun variants ----
            var allProcesses = Process.GetProcesses();
            foreach (var p in allProcesses)
            {
                string? procName;
                try { procName = p.ProcessName; }
                catch { continue; }

                bool isAweSun = string.Equals(procName, "AweSun", StringComparison.OrdinalIgnoreCase)
                             || string.Equals(procName, "awesun_guard", StringComparison.OrdinalIgnoreCase)
                             || string.Equals(procName, "AweSunService", StringComparison.OrdinalIgnoreCase);

                if (!isAweSun) continue;

                // Try to get full path
                string? path = null;
                try
                {
                    path = p.MainModule?.FileName;
                }
                catch { /* access denied — path remains null */ }

                if (path != null)
                {
                    if (path.Contains(SunloginAgentPath, StringComparison.OrdinalIgnoreCase))
                    {
                        hasAgent = true;
                    }
                    else if (path.Contains(SunloginClientPath, StringComparison.OrdinalIgnoreCase))
                    {
                        hasBackground = true;
                    }
                }
                else
                {
                    // Can't read path — treat as background (conservative)
                    hasBackground = true;
                }

                try { p.Dispose(); } catch { }
            }

            if (hasAgent) signals.Add("agent_process");
            if (hasBackground) signals.Add("background_process");

            // ---- Check for session window ----
            var windowTitles = GetVisibleWindowTitles();
            hasSessionWindow = windowTitles.Any(t => t.Contains(SessionWindowTitle));
            if (hasSessionWindow) signals.Add("session_window");

            // ---- Optional: loopback connections (only if AweSun processes exist) ----
            if (hasAgent || hasBackground)
            {
                int loopbackCount = CountSunloginLoopbackConnections();
                if (loopbackCount > 0) signals.Add("loopback_connection");
            }

            // ---- Determine result ----
            if (hasAgent || hasSessionWindow)
            {
                bool both = hasAgent && hasSessionWindow;
                return new DetectionResult
                {
                    IsDetected = true,
                    RemoteType = "sunlogin",
                    Source = (hasAgent && hasSessionWindow) ? "process,window"
                           : hasAgent ? "process" : "window",
                    Confidence = "high",
                    CheckedAt = NowStr(),
                    Message = both ? "已确认向日葵远程会话"
                            : hasAgent ? "检测到向日葵远程会话代理进程"
                            : "检测到向日葵远程会话窗口",
                    MatchedSignals = signals
                };
            }

            if (hasBackground || signals.Contains("loopback_connection"))
            {
                return new DetectionResult
                {
                    IsDetected = false,
                    RemoteType = "sunlogin",
                    Source = "process",
                    Confidence = "low",
                    CheckedAt = NowStr(),
                    Message = "向日葵后台运行，但未检测到远程会话",
                    MatchedSignals = signals
                };
            }

            return new DetectionResult
            {
                IsDetected = false,
                RemoteType = null,
                Source = "process",
                Confidence = "",
                CheckedAt = NowStr(),
                ErrorMessage = null
            };
        }
        catch (Exception ex)
        {
            return new DetectionResult
            {
                IsDetected = false, RemoteType = null, Source = "",
                Confidence = "", CheckedAt = NowStr(),
                ErrorMessage = $"Detection failed: {ex.Message}"
            };
        }
    }

    // ---- Win32 window enumeration (Unicode) ----
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowTextLength(IntPtr hWnd);

    private static List<string> GetVisibleWindowTitles()
    {
        var titles = new List<string>();
        EnumWindows((hWnd, _) =>
        {
            if (!IsWindowVisible(hWnd)) return true;
            int len = GetWindowTextLength(hWnd);
            if (len == 0) return true;
            var sb = new StringBuilder(len + 1);
            GetWindowText(hWnd, sb, sb.Capacity);
            var title = sb.ToString();
            if (!string.IsNullOrWhiteSpace(title))
                titles.Add(title);
            return true;
        }, IntPtr.Zero);
        return titles;
    }

    // ---- Network loopback detection ----
    private static int CountSunloginLoopbackConnections()
    {
        try
        {
            var connections = IPGlobalProperties
                .GetIPGlobalProperties()
                .GetActiveTcpConnections();

            return connections.Count(c =>
                IPAddress.IsLoopback(c.LocalEndPoint.Address) &&
                IPAddress.IsLoopback(c.RemoteEndPoint.Address) &&
                (c.LocalEndPoint.Port is >= 11200 and <= 11299 ||
                 c.LocalEndPoint.Port == 7635 ||
                 c.RemoteEndPoint.Port is >= 11200 and <= 11299 ||
                 c.RemoteEndPoint.Port == 7635));
        }
        catch
        {
            return 0;
        }
    }

    private static string NowStr() => DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
}

public class DetectionResult
{
    public bool IsDetected { get; set; }
    public string? RemoteType { get; set; }
    public string Source { get; set; } = "process";
    public string Confidence { get; set; } = "low";
    public string? ErrorMessage { get; set; }
    public string CheckedAt { get; set; } = "";
    public List<string> MatchedSignals { get; set; } = new();
    public string? Message { get; set; }
}
