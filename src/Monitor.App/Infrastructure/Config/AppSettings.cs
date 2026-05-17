using System.Text.Json;

namespace Monitor.App.Infrastructure.Config;

public class AppSettings
{
    public string? AdminPasswordHash { get; set; } = "";
    public string DefaultPassword { get; set; } = "123456";
    public string Theme { get; set; } = "light";
    public string BackupPath { get; set; } = "./backups";
    public int MaxDailyHours { get; set; } = 0;
    public string Language { get; set; } = "zh-CN";
    public bool AutoBackup { get; set; } = true;
    public int BackupRetentionDays { get; set; } = 30;
    public bool WindowAlwaysOnTop { get; set; } = true;
    public bool MinimizeToTray { get; set; } = true;
    public bool WebServerEnabled { get; set; } = true;
    public int WebServerPort { get; set; } = 8080;
    public string WebServerPassword { get; set; } = "123456";
    public bool RemoteMonitorEnabled { get; set; } = true;
    public int RemoteMonitorInterval { get; set; } = 3;
    public List<string> RemoteTools { get; set; } = new()
    {
        "SunloginClient.exe", "TeamViewer.exe", "AnyDesk.exe", "AnyDesk64.exe",
        "ToDesk.exe", "mstsc.exe", "msrdc.exe"
    };
    public bool TunnelEnabled { get; set; } = true;
    public string TunnelMode { get; set; } = "cloudflared";
    public string TunnelNgrokAuthToken { get; set; } = "";
    public string TunnelNgrokPath { get; set; } = "ngrok.exe";
    public string TunnelCloudflaredPath { get; set; } = "cloudflared.exe";
    public string CloudflareTunnelName { get; set; } = "monitor";
    public string CloudflareTunnelId { get; set; } = "";
    public string CloudflareHostname { get; set; } = "";
    public string OperatorRegistrationKey { get; set; } = "";
    public string OperatorRegistrationKeyHash { get; set; } = "";
    public bool OnboardingDismissed { get; set; } = false;

    private static readonly string _configPath = AppPaths.ConfigPath;

    public static AppSettings Load()
    {
        if (File.Exists(_configPath))
        {
            var json = File.ReadAllText(_configPath);
            var settings = JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();

            // Phase 6: snake_case fallback for operator_registration_key
            if (string.IsNullOrEmpty(settings.OperatorRegistrationKey))
            {
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty("operator_registration_key", out var el))
                    settings.OperatorRegistrationKey = el.GetString() ?? "";
                if (string.IsNullOrEmpty(settings.OperatorRegistrationKeyHash)
                    && doc.RootElement.TryGetProperty("operator_registration_key_hash", out var hashEl))
                    settings.OperatorRegistrationKeyHash = hashEl.GetString() ?? "";
            }

            settings.MergeDefaults();
            settings.MigratePlainRegistrationKey();
            return settings;
        }
        var created = new AppSettings();
        created.MergeDefaults();
        return created;
    }

    public void Save()
    {
        if (!string.IsNullOrEmpty(OperatorRegistrationKeyHash))
            OperatorRegistrationKey = "";

        Directory.CreateDirectory(Path.GetDirectoryName(_configPath)!);
        var json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(_configPath, json);
    }

    private void MergeDefaults()
    {
        var defaults = new AppSettings();
        if (string.IsNullOrEmpty(WebServerPassword)) WebServerPassword = defaults.WebServerPassword;
        if (RemoteTools == null || RemoteTools.Count == 0) RemoteTools = defaults.RemoteTools;
        if (string.IsNullOrEmpty(TunnelMode)) TunnelMode = defaults.TunnelMode;
        if (string.IsNullOrEmpty(TunnelCloudflaredPath)) TunnelCloudflaredPath = defaults.TunnelCloudflaredPath;
        if (string.IsNullOrEmpty(TunnelNgrokPath)) TunnelNgrokPath = defaults.TunnelNgrokPath;
        if (string.IsNullOrEmpty(CloudflareTunnelName)) CloudflareTunnelName = defaults.CloudflareTunnelName;
        if (string.IsNullOrWhiteSpace(BackupPath) || !Path.IsPathRooted(BackupPath))
            BackupPath = AppPaths.BackupDirectory;
    }

    private void MigratePlainRegistrationKey()
    {
        if (string.IsNullOrWhiteSpace(OperatorRegistrationKey) || !string.IsNullOrWhiteSpace(OperatorRegistrationKeyHash))
            return;

        OperatorRegistrationKeyHash = BCrypt.Net.BCrypt.HashPassword(OperatorRegistrationKey.Trim());
        OperatorRegistrationKey = "";
        Save();
    }

    public string Get(string key, string defaultValue = "")
    {
        return key switch
        {
            "web_server_password" => WebServerPassword,
            "web_server_port" => WebServerPort.ToString(),
            "web_server_enabled" => WebServerEnabled.ToString().ToLower(),
            "tunnel_enabled" => TunnelEnabled.ToString().ToLower(),
            "tunnel_mode" => TunnelMode,
            "cloudflare_hostname" => CloudflareHostname,
            "cloudflare_tunnel_name" => CloudflareTunnelName,
            "cloudflare_tunnel_id" => CloudflareTunnelId,
            "operator_registration_key_hash" => OperatorRegistrationKeyHash,
            "onboarding_dismissed" => OnboardingDismissed.ToString().ToLower(),
            "auto_backup" => AutoBackup.ToString().ToLower(),
            "backup_retention_days" => BackupRetentionDays.ToString(),
            "remote_monitor_enabled" => RemoteMonitorEnabled.ToString().ToLower(),
            "theme" => Theme,
            "language" => Language,
            "admin_password_hash" => AdminPasswordHash ?? "",
            "default_password" => DefaultPassword,
            _ => defaultValue
        };
    }

    public void Set(string key, string value)
    {
        switch (key)
        {
            case "web_server_password": WebServerPassword = value; break;
            case "web_server_port": WebServerPort = int.Parse(value); break;
            case "web_server_enabled": WebServerEnabled = bool.Parse(value); break;
            case "tunnel_enabled": TunnelEnabled = bool.Parse(value); break;
            case "tunnel_mode": TunnelMode = value; break;
            case "cloudflare_hostname": CloudflareHostname = value; break;
            case "cloudflare_tunnel_name": CloudflareTunnelName = value; break;
            case "cloudflare_tunnel_id": CloudflareTunnelId = value; break;
            case "operator_registration_key_hash": OperatorRegistrationKeyHash = value; OperatorRegistrationKey = ""; break;
            case "onboarding_dismissed": OnboardingDismissed = bool.Parse(value); break;
            case "auto_backup": AutoBackup = bool.Parse(value); break;
            case "backup_retention_days": BackupRetentionDays = int.Parse(value); break;
            case "remote_monitor_enabled": RemoteMonitorEnabled = bool.Parse(value); break;
            case "theme": Theme = value; break;
            case "language": Language = value; break;
            case "admin_password_hash": AdminPasswordHash = value; break;
            case "default_password": DefaultPassword = value; break;
        }
        Save();
    }
}
