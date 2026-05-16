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

        var appDir = AppDomain.CurrentDomain.BaseDirectory;
        CopyFileIfNeeded(Path.Combine(appDir, "config.json"), ConfigPath);
        CopyFileIfNeeded(Path.Combine(appDir, "monitor.db"), DatabasePath);
        CopyDirectoryIfNeeded(Path.Combine(appDir, "backups"), BackupDirectory);
        CopyLogFilesIfNeeded(appDir);
    }

    private static void CopyFileIfNeeded(string source, string target)
    {
        if (!File.Exists(source) || File.Exists(target))
            return;

        File.Copy(source, target, overwrite: false);
    }

    private static void CopyDirectoryIfNeeded(string source, string target)
    {
        if (!Directory.Exists(source))
            return;

        Directory.CreateDirectory(target);

        foreach (var file in Directory.EnumerateFiles(source))
        {
            var targetFile = Path.Combine(target, Path.GetFileName(file));
            if (!File.Exists(targetFile))
                File.Copy(file, targetFile, overwrite: false);
        }
    }

    private static void CopyLogFilesIfNeeded(string appDir)
    {
        foreach (var file in Directory.EnumerateFiles(appDir, "app*.log"))
        {
            var targetFile = Path.Combine(LogDirectory, Path.GetFileName(file));
            if (!File.Exists(targetFile))
                File.Copy(file, targetFile, overwrite: false);
        }
    }
}
