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

        group.MapGet("/", (HttpRequest request, WebAccessService auth, AppSettings cfg) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);
            return Results.Ok(new
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
            });
        });

        group.MapPost("/password/admin", (HttpRequest request, WebAccessService auth,
            AdminPasswordRequest req, AppSettings cfg) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);
            var ok = PasswordManager.ChangeAdminPassword(cfg, req.OldPassword, req.NewPassword);
            return ok
                ? Results.Ok(new { success = true })
                : Results.Json(new { detail = "old password incorrect" }, statusCode: 403);
        });

        group.MapPost("/password/web", (HttpRequest request, WebAccessService auth,
            WebPasswordRequest req, AppSettings cfg) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);
            cfg.WebServerPassword = req.NewPassword;
            cfg.Save();
            return Results.Ok(new { success = true });
        });

        group.MapPost("/backup", (HttpRequest request, WebAccessService auth, BackupService svc) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);
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

        group.MapGet("/backups", (HttpRequest request, WebAccessService auth, BackupService svc) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);
            var list = svc.GetBackupList();
            return Results.Ok(new { backups = list });
        });

        group.MapGet("/operator-registration-key", (HttpRequest request, WebAccessService auth, AppSettings cfg) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);
            return Results.Ok(new { has_registration_key = !string.IsNullOrEmpty(cfg.OperatorRegistrationKey) });
        });

        group.MapPost("/operator-registration-key", async (HttpRequest request,
            WebAccessService auth, AppSettings cfg) =>
        {
            if (!TryGetToken(request, auth)) return Results.Json(new { detail = "unauthorized" }, statusCode: 401);

            Dictionary<string, string>? body;
            try { body = await request.ReadFromJsonAsync<Dictionary<string, string>>(); }
            catch { return Results.BadRequest(new { detail = "invalid request body" }); }

            if (body == null || !body.TryGetValue("registration_key", out var key) || string.IsNullOrWhiteSpace(key))
                return Results.BadRequest(new { detail = "registration_key is required" });

            if (key.Trim().Length < 4)
                return Results.BadRequest(new { detail = "登记码长度至少 4 个字符" });

            cfg.OperatorRegistrationKey = key.Trim();
            cfg.Save();
            return Results.Ok(new { success = true });
        });
    }

    private static bool TryGetToken(HttpRequest request, WebAccessService auth)
    {
        var header = request.Headers["Authorization"].FirstOrDefault();
        if (!string.IsNullOrEmpty(header) && header.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
            return auth.ValidateToken(header.Substring(7));
        return false;
    }
}

public record AdminPasswordRequest(string OldPassword, string NewPassword);
public record WebPasswordRequest(string NewPassword);
