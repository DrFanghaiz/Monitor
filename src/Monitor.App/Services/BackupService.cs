using System.IO.Compression;
using Microsoft.Data.Sqlite;
using Monitor.App.Infrastructure.Config;
using Serilog;

namespace Monitor.App.Services;

public class BackupService
{
    private readonly AppSettings _settings;
    private readonly string _backupDir;
    private readonly string _dbPath;
    private readonly string _configPath;

    public BackupService(AppSettings settings, string dbPath, string configPath)
    {
        _settings = settings;
        _dbPath = dbPath;
        _configPath = configPath;
        _backupDir = settings.BackupPath;
        if (!Path.IsPathRooted(_backupDir))
            _backupDir = Path.Combine(AppPaths.DataDirectory, _backupDir);
        Directory.CreateDirectory(_backupDir);
    }

    public string CreateBackup(bool manual = false)
    {
        var prefix = manual ? "manual_backup" : "auto_backup";
        var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
        var fileName = $"{prefix}_{timestamp}.zip";
        var filePath = Path.Combine(_backupDir, fileName);
        var tempDir = Path.Combine(Path.GetTempPath(), $"monitor_backup_{Guid.NewGuid():N}");

        try
        {
            Directory.CreateDirectory(tempDir);

            // Use SQLite online backup API — safe while DB is in use
            if (File.Exists(_dbPath))
            {
                var tempDb = Path.Combine(tempDir, Path.GetFileName(_dbPath));
                BackupDatabase(_dbPath, tempDb);
            }

            // Copy config alongside
            if (File.Exists(_configPath))
            {
                var tempConfig = Path.Combine(tempDir, Path.GetFileName(_configPath));
                File.Copy(_configPath, tempConfig, overwrite: true);
            }

            // Verify we have files to back up
            var files = Directory.GetFiles(tempDir);
            if (files.Length == 0)
            {
                Directory.Delete(tempDir, recursive: true);
                throw new InvalidOperationException("no files to backup");
            }

            // Create zip from temp files
            if (File.Exists(filePath)) File.Delete(filePath);
            ZipFile.CreateFromDirectory(tempDir, filePath, CompressionLevel.Optimal, includeBaseDirectory: false);

            if (!manual)
                CleanupOldBackups();

            Log.Information("Backup created: {Path} ({Size} bytes)", filePath, new FileInfo(filePath).Length);
            return filePath;
        }
        catch (Exception ex)
        {
            // Clean up on failure — no empty zip
            if (File.Exists(filePath))
            {
                try { File.Delete(filePath); } catch { }
            }
            Log.Error(ex, "Backup failed");
            throw;
        }
        finally
        {
            if (Directory.Exists(tempDir))
            {
                try { Directory.Delete(tempDir, recursive: true); } catch { }
            }
        }
    }

    private static void BackupDatabase(string sourcePath, string destPath)
    {
        using var source = new SqliteConnection($"Data Source={sourcePath}");
        source.Open();
        using (var dest = new SqliteConnection($"Data Source={destPath}"))
        {
            dest.Open();
            source.BackupDatabase(dest);
            dest.Close();
        }
        SqliteConnection.ClearAllPools();
    }

    public List<BackupEntry> GetBackupList()
    {
        var entries = new List<BackupEntry>();
        var dir = new DirectoryInfo(_backupDir);
        foreach (var file in dir.GetFiles("*.zip").OrderByDescending(f => f.CreationTime))
        {
            entries.Add(new BackupEntry
            {
                Name = file.Name,
                Path = file.FullName,
                Size = file.Length,
                Created = file.CreationTime.ToString("yyyy-MM-dd HH:mm:ss"),
                IsManual = file.Name.StartsWith("manual_")
            });
        }
        return entries;
    }

    public bool ShouldAutoBackup()
    {
        if (!_settings.AutoBackup) return false;
        var todayPrefix = $"auto_backup_{DateTime.Now:yyyyMMdd}";
        return !Directory.GetFiles(_backupDir, $"{todayPrefix}*").Any();
    }

    public void AutoBackupIfNeeded()
    {
        if (ShouldAutoBackup())
            CreateBackup(manual: false);
    }

    private void CleanupOldBackups()
    {
        var cutoff = DateTime.Now.AddDays(-_settings.BackupRetentionDays);
        foreach (var file in Directory.GetFiles(_backupDir, "auto_backup_*.zip"))
        {
            if (File.GetLastWriteTime(file) < cutoff)
                File.Delete(file);
        }
    }
}

public class BackupEntry
{
    public string Name { get; set; } = "";
    public string Path { get; set; } = "";
    public long Size { get; set; }
    public string Created { get; set; } = "";
    public bool IsManual { get; set; }
}
