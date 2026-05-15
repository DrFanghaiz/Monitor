using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Infrastructure.Config;
using Monitor.App.Repositories;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class RemoteEndpoints
{
    public static void MapRemoteEndpoints(this WebApplication app)
    {
        app.MapPost("/api/remote/operator", async (HttpRequest request,
            RemoteMonitorService monitor, WebAccessService auth) =>
        {
            // Auth check
            if (!TryGetValidToken(request, auth, out _))
                return Results.Json(new { detail = "unauthorized" }, statusCode: 401);

            OperatorRequest? body;
            try
            {
                body = await request.ReadFromJsonAsync<OperatorRequest>();
            }
            catch
            {
                return Results.BadRequest(new { detail = "invalid request body" });
            }

            if (body == null || string.IsNullOrWhiteSpace(body.OperatorName))
                return Results.BadRequest(new { detail = "operator_name 不能为空" });

            var trimmed = body.OperatorName.Trim();
            if (trimmed.Length < 2 || trimmed.Length > 30)
                return Results.BadRequest(new { detail = "操作人姓名长度 2-30 个字符" });

            if (monitor.TrySetOperatorName(trimmed, out var error))
                return Results.Ok(new { success = true, operator_name = trimmed });

            return Results.Json(new { detail = error }, statusCode: 409);
        });

        app.MapGet("/api/remote/operator/register/available", (AppSettings cfg) =>
        {
            return Results.Ok(new { available = !string.IsNullOrEmpty(cfg.OperatorRegistrationKey) });
        });

        // Public registration: requires registration_key, not admin token
        app.MapPost("/api/remote/operator/register", async (HttpRequest request,
            RemoteMonitorService monitor, AppSettings cfg) =>
        {
            if (string.IsNullOrEmpty(cfg.OperatorRegistrationKey))
                return Results.Json(new { detail = "registration not available" }, statusCode: 401);

            RegistrationRequest? body;
            try { body = await request.ReadFromJsonAsync<RegistrationRequest>(); }
            catch { return Results.BadRequest(new { detail = "invalid request body" }); }

            if (body == null || body.RegistrationKey != cfg.OperatorRegistrationKey)
                return Results.Json(new { detail = "unauthorized" }, statusCode: 401);

            if (string.IsNullOrWhiteSpace(body.OperatorName))
                return Results.BadRequest(new { detail = "operator_name 不能为空" });

            var trimmed = body.OperatorName.Trim();
            if (trimmed.Length < 2 || trimmed.Length > 30)
                return Results.BadRequest(new { detail = "操作人姓名长度 2-30 个字符" });

            if (monitor.TrySetOperatorName(trimmed, out var error))
                return Results.Ok(new { success = true, operator_name = trimmed });

            return Results.Json(new { detail = error }, statusCode: 409);
        });

        app.MapGet("/api/remote/sessions", (HttpRequest request,
            IRemoteSessionRepository repo, WebAccessService auth) =>
        {
            if (!TryGetValidToken(request, auth, out _))
                return Results.Json(new { detail = "unauthorized" }, statusCode: 401);

            var limitStr = request.Query["limit"].FirstOrDefault() ?? "20";
            if (!int.TryParse(limitStr, out var limit) || limit < 1 || limit > 100)
                limit = 20;

            var sessions = repo.GetRecentRemoteSessions(limit);
            return Results.Ok(new { sessions });
        });
    }

    private static bool TryGetValidToken(HttpRequest request, WebAccessService auth, out string token)
    {
        token = "";
        var header = request.Headers["Authorization"].FirstOrDefault();
        if (!string.IsNullOrEmpty(header) && header.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            token = header.Substring(7);
            return auth.ValidateToken(token);
        }
        return false;
    }
}

public record OperatorRequest(string OperatorName);
public record RegistrationRequest(string OperatorName, string RegistrationKey);
