using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Infrastructure.Config;
using Monitor.App.Infrastructure.Security;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class SettingsEndpoints
{
    public static void MapSettingsEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/settings");

        group.MapGet("/", (AppSettings cfg) => Results.Ok(new
        {
            web_server_port = cfg.WebServerPort,
            web_server_enabled = cfg.WebServerEnabled,
            tunnel_enabled = cfg.TunnelEnabled,
            tunnel_mode = cfg.TunnelMode,
            auto_backup = cfg.AutoBackup,
            backup_retention_days = cfg.BackupRetentionDays,
            remote_monitor_enabled = cfg.RemoteMonitorEnabled,
            theme = cfg.Theme,
            language = cfg.Language
        }));

        group.MapPost("/password/admin", (AdminPasswordRequest req, AppSettings cfg) =>
        {
            var ok = PasswordManager.ChangeAdminPassword(cfg, req.OldPassword, req.NewPassword);
            return ok
                ? Results.Ok(new { success = true })
                : Results.Json(new { detail = "old password incorrect" }, statusCode: 403);
        });

        group.MapPost("/password/web", (WebPasswordRequest req, AppSettings cfg) =>
        {
            cfg.WebServerPassword = req.NewPassword;
            cfg.Save();
            return Results.Ok(new { success = true });
        });

        group.MapPost("/backup", (BackupService svc) =>
        {
            try
            {
                var path = svc.CreateBackup(manual: true);
                return Results.Ok(new { success = true, path });
            }
            catch (Exception ex)
            {
                return Results.Json(new { detail = ex.Message }, statusCode: 500);
            }
        });

        group.MapGet("/backups", (BackupService svc) =>
        {
            var list = svc.GetBackupList();
            return Results.Ok(new { backups = list });
        });
    }
}

public record AdminPasswordRequest(string OldPassword, string NewPassword);
public record WebPasswordRequest(string NewPassword);
