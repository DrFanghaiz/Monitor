using System;
using System.IO;

namespace Monitor.App.Infrastructure.Config;

public static class AppPaths
{
    public static string DataDirectory { get; } =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "Monitor");

    public static string ConfigPath => Path.Combine(DataDirectory, "config.json");
    public static string DatabasePath => Path.Combine(DataDirectory, "monitor.db");
    public static string BackupDirectory => Path.Combine(DataDirectory, "backups");
    public static string LogDirectory => Path.Combine(DataDirectory, "logs");
    public static string LogPath => Path.Combine(LogDirectory, "app.log");

    public static void EnsureDataDirectory()
    {
        Directory.CreateDirectory(DataDirectory);
        Directory.CreateDirectory(BackupDirectory);
        Directory.CreateDirectory(LogDirectory);
    }
}
