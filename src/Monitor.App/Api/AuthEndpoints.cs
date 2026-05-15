using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class AuthEndpoints
{
    public static void MapAuthEndpoints(this WebApplication app)
    {
        app.MapPost("/api/auth", async (HttpRequest request, WebAccessService auth) =>
        {
            Dictionary<string, string>? body;
            try
            {
                body = await request.ReadFromJsonAsync<Dictionary<string, string>>();
            }
            catch
            {
                return Results.BadRequest(new { detail = "invalid request body" });
            }

            if (body == null || !body.TryGetValue("password", out var password))
                return Results.BadRequest(new { detail = "password is required" });

            var remoteIp = request.HttpContext.Connection.RemoteIpAddress?.ToString();

            if (auth.IsLoginLocked(remoteIp))
                return Results.Json(new { detail = "too many attempts, try later" }, statusCode: 429);

            var token = auth.Authenticate(password, remoteIp);
            if (token != null)
                return Results.Ok(new { success = true, token });

            return Results.Json(new { detail = "invalid password" }, statusCode: 401);
        });
    }
}
