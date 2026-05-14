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

            var token = auth.Authenticate(password);
            return token != null
                ? Results.Ok(new { success = true, token })
                : Results.Json(new { detail = "invalid password" }, statusCode: 401);
        });
    }
}
