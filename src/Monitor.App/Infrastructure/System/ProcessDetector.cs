using System.Diagnostics;
using System.Net;
using System.Net.NetworkInformation;
using System.Runtime.InteropServices;
using System.Text;

namespace Monitor.App.Infrastructure.System;

/// <summary>
/// 远程占用检测器：覆盖本机部署的三种远控工具 —— 向日葵(Sunlogin/AweSun)、ToDesk、UU远程(UURemote)。
///
/// 判定原则：
///  - 只有检测到"会话级"信号才认为占用（IsDetected=true）；
///  - 仅"后台进程在运行"（软件常驻、无人连接）不算占用，只作为低置信度提示，
///    避免 ToDesk/UU 常驻导致状态永远显示"占用"；
///  - 多个工具同时被控时，ActiveToolNames 会列出全部工具，RemoteType 用 " + " 连接。
/// 多信号：会话进程名 + 会话窗口标题（+ 向日葵回环端口）。
/// </summary>
public class ProcessDetector
{
    private sealed class ToolSpec
    {
        public string Id { get; init; } = "";
        public string DisplayName { get; init; } = "";
        /// <summary>后台常驻进程名（不含 .exe，忽略大小写）。仅作低置信度提示。</summary>
        public string[] BackgroundProcesses { get; init; } = Array.Empty<string>();
        /// <summary>出现即代表"会话"的进程名。</summary>
        public string[] SessionProcesses { get; init; } = Array.Empty<string>();
        /// <summary>命中即可视窗口标题即代表"会话"的关键词。</summary>
        public string[] WindowKeywords { get; init; } = Array.Empty<string>();
        /// <summary>是否为向日葵（需要按路径判断 agent 进程）。</summary>
        public bool IsSunlogin { get; init; }
        /// <summary>是否排除与关键词完全相同的窗口标题（避免把主界面当成会话）。</summary>
        public bool ExcludeExactWindowTitle { get; init; }
    }

    private static readonly ToolSpec[] Tools =
    {
        new()
        {
            Id = "sunlogin", DisplayName = "向日葵", IsSunlogin = true,
            BackgroundProcesses = new[] { "AweSun", "awesun_guard", "AweSunService" },
            SessionProcesses = Array.Empty<string>(),
            WindowKeywords = new[] { "向日葵-远程会话", "向日葵远程会话", "向日葵-控制" }
        },
        new()
        {
            Id = "todesk", DisplayName = "ToDesk",
            BackgroundProcesses = new[] { "ToDesk", "ToDesk_Service", "ToDeskClient" },
            SessionProcesses = new[] { "ToDesk_Session" },
            WindowKeywords = new[] { "ToDesk远程控制", "ToDesk - 远程控制", "正在被远程控制" },
            ExcludeExactWindowTitle = true
        },
        new()
        {
            // 网易UU远程基于 GameViewer 内核：GameViewer / GameViewerServer 等常驻后台，
            // 主界面窗口标题为“网易UU远程”，绝不能当作会话（否则空闲也误报占用）。
            // 会话级信号：uuyc-mux 串流进程，或明确的“正在被远程控制”提示窗口。
            Id = "uuremote", DisplayName = "UU远程",
            BackgroundProcesses = new[] { "GameViewer", "GameViewerServer", "GameViewerService", "GameViewerHealthd", "GameViewerLauncher", "uuyc-cli", "uuyc-mux" },
            SessionProcesses = new[] { "uuyc-mux" },
            // GameViewerPrivateWindowName：UU 被控时（隐私屏/连接窗口）出现的内部窗口标题。
            WindowKeywords = new[] { "GameViewerPrivateWindowName", "正在被远程控制", "远程控制中", "UU远程控制" },
            ExcludeExactWindowTitle = false
        }
    };

    // 向日葵 agent 子路径（会话进程按路径区分）
    private const string SunloginAgentPath = @"\SunloginClient\agent\";

    public ProcessDetector() { }

    public DetectionResult Detect()
    {
        try
        {
            var windowTitles = GetVisibleWindowTitles();

            // ---- 一次性快照所有进程名 ----
            var procNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var all = Process.GetProcesses();
            try
            {
                foreach (var p in all)
                {
                    try { procNames.Add(p.ProcessName); } catch { }
                }
            }
            finally
            {
                foreach (var p in all) { try { p.Dispose(); } catch { } }
            }

            var activeTools = new List<string>();
            var activeIds = new List<string>();
            var runningOnly = new List<string>();
            var signals = new List<string>();

            foreach (var tool in Tools)
            {
                bool hasSessionProcess = tool.SessionProcesses.Any(n => procNames.Contains(n));
                if (tool.IsSunlogin && !hasSessionProcess)
                    hasSessionProcess = HasSunloginAgentProcess();

                bool hasBackground = tool.BackgroundProcesses.Any(n => procNames.Contains(n));
                bool hasSessionWindow = windowTitles.Any(t => MatchWindow(t, tool));

                // ToDesk 会话实测特征（2026-10 版本）：被控时会由服务进程再派生一个 ToDesk.exe
                // 会话进程（命令行/路径可能不可见），它会与对端建立非 443 的公网 TCP 连接；
                // 空闲时常驻仅 2 个 ToDesk.exe（服务 + 带 --show 的界面进程）。故用两种信号兜底：
                //   a) ToDesk.exe 进程数 >= 3；b) 某个 ToDesk 进程存在非回环、非 443 的已建立 TCP 连接。
                bool hasTcpSession = tool.Id == "todesk" && HasTodeskSessionSignal();

                // UU远程 会话实测特征（2026-10 版 4.44）：GameViewerServer 被控时会新增会话监听端口
                // 与多条到中继的 443 连接（详见 HasUuSessionSignal 注释）。
                bool hasUuSession = tool.Id == "uuremote" && HasUuSessionSignal();

                bool active = hasSessionProcess || hasSessionWindow || hasTcpSession || hasUuSession;

                if (active)
                {
                    activeIds.Add(tool.Id);
                    activeTools.Add(tool.DisplayName);
                    if (hasSessionProcess) signals.Add($"{tool.Id}:process");
                    if (hasSessionWindow) signals.Add($"{tool.Id}:window");
                    if (hasTcpSession) signals.Add($"{tool.Id}:tcp");
                    if (hasUuSession) signals.Add($"{tool.Id}:session");
                }
                else if (hasBackground)
                {
                    runningOnly.Add(tool.DisplayName);
                }
            }

            // 向日葵回环端口（仅在已判为向日葵占用时补充信号）
            if (activeIds.Contains("sunlogin") && CountSunloginLoopbackConnections() > 0)
                signals.Add("sunlogin:loopback");

            if (activeTools.Count > 0)
            {
                bool anyWindow = signals.Any(s => s.EndsWith(":window", StringComparison.Ordinal));
                return new DetectionResult
                {
                    IsDetected = true,
                    RemoteType = string.Join(" + ", activeTools),
                    ActiveToolIds = activeIds,
                    ActiveToolNames = activeTools,
                    RunningToolNames = runningOnly,
                    Source = anyWindow ? "process,window" : "process",
                    Confidence = "high",
                    CheckedAt = NowStr(),
                    Message = activeTools.Count == 1
                        ? $"检测到 {activeTools[0]} 远程会话"
                        : $"检测到多个远程会话：{string.Join("、", activeTools)}",
                    MatchedSignals = signals
                };
            }

            if (runningOnly.Count > 0)
            {
                return new DetectionResult
                {
                    IsDetected = false,
                    RemoteType = null,
                    ActiveToolIds = new List<string>(),
                    ActiveToolNames = new List<string>(),
                    RunningToolNames = runningOnly,
                    Source = "process",
                    Confidence = "low",
                    CheckedAt = NowStr(),
                    Message = $"{string.Join("、", runningOnly)} 正在后台运行，未检测到远程会话",
                    MatchedSignals = new List<string> { "background_process" }
                };
            }

            return new DetectionResult
            {
                IsDetected = false,
                RemoteType = null,
                ActiveToolIds = new List<string>(),
                ActiveToolNames = new List<string>(),
                RunningToolNames = new List<string>(),
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

    private static bool MatchWindow(string title, ToolSpec tool)
    {
        foreach (var kw in tool.WindowKeywords)
        {
            if (!title.Contains(kw, StringComparison.OrdinalIgnoreCase)) continue;
            if (tool.ExcludeExactWindowTitle
                && string.Equals(title.Trim(), kw, StringComparison.OrdinalIgnoreCase))
                continue;
            return true;
        }
        return false;
    }

    private static bool HasSunloginAgentProcess()
    {
        foreach (var p in Process.GetProcesses())
        {
            try
            {
                var name = p.ProcessName;
                if (!(string.Equals(name, "AweSun", StringComparison.OrdinalIgnoreCase)
                      || string.Equals(name, "awesun_guard", StringComparison.OrdinalIgnoreCase)
                      || string.Equals(name, "AweSunService", StringComparison.OrdinalIgnoreCase)))
                    continue;

                string? path = null;
                try { path = p.MainModule?.FileName; } catch { }
                if (path != null && path.Contains(SunloginAgentPath, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            catch { }
            finally { try { p.Dispose(); } catch { } }
        }
        return false;
    }

    // ---- Win32 窗口枚举（Unicode）----
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
        try
        {
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
        }
        catch { /* 枚举失败时返回已收集的标题 */ }
        return titles;
    }

    // ---- 回环端口检测（向日葵）----
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

    // ---- ToDesk 会话检测：进程数量 + 非 443 公网已建立连接 ----
    private const int AF_INET = 2;
    private const int TCP_TABLE_OWNER_PID_CONNECTIONS = 4;
    private const uint MIB_TCP_STATE_LISTEN = 2;
    private const uint MIB_TCP_STATE_ESTAB = 5;

    [StructLayout(LayoutKind.Sequential)]
    private struct MIB_TCPROW_OWNER_PID
    {
        public uint State;
        public uint LocalAddr;
        public uint LocalPort;
        public uint RemoteAddr;
        public uint RemotePort;
        public uint OwningPid;
    }

    [DllImport("iphlpapi.dll", SetLastError = true)]
    private static extern uint GetExtendedTcpTable(IntPtr pTcpTable, ref int pdwSize, bool bOrder,
        int ulAf, int tableClass, uint reserved);

    private static bool HasTodeskSessionSignal()
    {
        Process[] procs;
        try { procs = Process.GetProcessesByName("ToDesk"); }
        catch { return false; }

        try
        {
            // 空闲常驻一般 2 个 ToDesk.exe（服务 + 带 --show 的界面进程）；被控时多出会话进程。
            if (procs.Length >= 3) return true;

            var pids = new HashSet<uint>();
            foreach (var p in procs)
            {
                try { pids.Add((uint)p.Id); } catch { }
            }
            if (pids.Count == 0) return false;

            foreach (var (state, remoteAddr, remotePort, pid) in GetTcpRows())
            {
                if (state != MIB_TCP_STATE_ESTAB) continue;
                if (!pids.Contains(pid)) continue;
                if (remotePort == 443) continue; // 排除到云端的控制通道（空闲也有）
                IPAddress ip;
                try { ip = new IPAddress((long)remoteAddr); } catch { continue; }
                if (IPAddress.IsLoopback(ip)) continue;
                return true;
            }
        }
        finally
        {
            foreach (var p in procs) { try { p.Dispose(); } catch { } }
        }
        return false;
    }

    private static List<(uint State, uint RemoteAddr, int RemotePort, uint Pid)> GetTcpRows()
    {
        var result = new List<(uint State, uint RemoteAddr, int RemotePort, uint Pid)>();
        int size = 0;
        GetExtendedTcpTable(IntPtr.Zero, ref size, false, AF_INET, TCP_TABLE_OWNER_PID_CONNECTIONS, 0);
        if (size <= 0) return result;

        IntPtr buffer = Marshal.AllocHGlobal(size);
        try
        {
            uint ret = GetExtendedTcpTable(buffer, ref size, false, AF_INET, TCP_TABLE_OWNER_PID_CONNECTIONS, 0);
            if (ret != 0) return result;

            int count = Marshal.ReadInt32(buffer);
            IntPtr rowPtr = IntPtr.Add(buffer, 4);
            int rowSize = Marshal.SizeOf<MIB_TCPROW_OWNER_PID>();
            for (int i = 0; i < count; i++)
            {
                var row = Marshal.PtrToStructure<MIB_TCPROW_OWNER_PID>(rowPtr);
                int remotePort = IPAddress.NetworkToHostOrder((short)(row.RemotePort & 0xFFFF));
                result.Add((row.State, row.RemoteAddr, remotePort, row.OwningPid));
                rowPtr = IntPtr.Add(rowPtr, rowSize);
            }
        }
        finally
        {
            Marshal.FreeHGlobal(buffer);
        }
        return result;
    }

    /// <summary>
    /// UU远程(UU 4.44 / GameViewer)被控会话实测特征：
    ///  - 空闲：GameViewerServer 约 2 个监听端口、1 条到云端 443 的连接；
    ///  - 被控：GameViewerServer 新增 3 个会话监听端口（如 13411/13412/13414），
    ///          并多出约 6 条到中继 183.201.236.x:443 的已建立连接。
    /// 判定：GameViewerServer 监听端口数 >= 4，或到公网 443 的已建立连接数 >= 3。
    /// </summary>
    private static bool HasUuSessionSignal()
    {
        Process[] procs;
        try { procs = Process.GetProcessesByName("GameViewerServer"); }
        catch { return false; }

        try
        {
            if (procs.Length == 0) return false;

            var pids = new HashSet<uint>();
            foreach (var p in procs)
            {
                try { pids.Add((uint)p.Id); } catch { }
            }

            int listenCount = 0;
            int estRemote443 = 0;
            foreach (var (state, remoteAddr, remotePort, pid) in GetTcpRows())
            {
                if (!pids.Contains(pid)) continue;

                if (state == MIB_TCP_STATE_LISTEN)
                {
                    listenCount++;
                    continue;
                }
                if (state != MIB_TCP_STATE_ESTAB) continue;
                if (remotePort != 443) continue;
                IPAddress ip;
                try { ip = new IPAddress((long)remoteAddr); } catch { continue; }
                if (IPAddress.IsLoopback(ip)) continue;
                estRemote443++;
            }

            return listenCount >= 4 || estRemote443 >= 3;
        }
        finally
        {
            foreach (var p in procs) { try { p.Dispose(); } catch { } }
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

    /// <summary>当前处于"会话"状态的工具 id 列表（如 sunlogin/todesk/uuremote）。</summary>
    public List<string> ActiveToolIds { get; set; } = new();
    /// <summary>当前处于"会话"状态的工具显示名列表。</summary>
    public List<string> ActiveToolNames { get; set; } = new();
    /// <summary>仅后台运行、未确认会话的工具显示名列表。</summary>
    public List<string> RunningToolNames { get; set; } = new();
}
