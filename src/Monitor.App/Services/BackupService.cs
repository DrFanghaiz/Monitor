using System.IO.Compression;
using Monitor.App.Infrastructure.Config;

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
            _backupDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, _backupDir);
        Directory.CreateDirectory(_backupDir);
    }

    public string CreateBackup(bool manual = false)
    {
        var prefix = manual ? "manual_backup" : "auto_backup";
        var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
        var fileName = $"{prefix}_{timestamp}.zip";
        var filePath = Path.Combine(_backupDir, fileName);

        using var zip = ZipFile.Open(filePath, ZipArchiveMode.Create);
        if (File.Exists(_dbPath))
            zip.CreateEntryFromFile(_dbPath, Path.GetFileName(_dbPath));
        if (File.Exists(_configPath))
            zip.CreateEntryFromFile(_configPath, Path.GetFileName(_configPath));

        if (!manual)
            CleanupOldBackups();

        return filePath;
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
