using System.Diagnostics;

namespace Monitor.App.Infrastructure.System;

/// <summary>
/// Detects running remote-control tools (AnyDesk, TeamViewer, etc.).
/// Port of Python remote_monitor.py _check_processes().
/// </summary>
public class ProcessDetector
{
    private readonly List<string> _processNames;

    public ProcessDetector(List<string> processNames)
    {
        _processNames = processNames;
    }

    /// <summary>
    /// Check which configured remote tools are currently running.
    /// Returns the first matched process name, or null if none found.
    /// </summary>
    public string? Detect()
    {
        foreach (var name in _processNames)
        {
            var baseName = Path.GetFileNameWithoutExtension(name);
            var processes = Process.GetProcessesByName(baseName);
            if (processes.Length > 0)
            {
                // Map back to the configured display name
                return name switch
                {
                    "SunloginClient.exe" => "sunlogin",
                    "TeamViewer.exe" => "teamviewer",
                    "AnyDesk.exe" or "AnyDesk64.exe" => "anydesk",
                    "ToDesk.exe" => "todesk",
                    "mstsc.exe" => "mstsc",
                    "msrdc.exe" => "msrdc",
                    _ => baseName.ToLower()
                };
            }
        }
        return null;
    }
}
