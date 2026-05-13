using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class AuthEndpoints
{
    public static void MapAuthEndpoints(this WebApplication app)
    {
        app.MapPost("/api/auth", (HttpRequest request, WebAccessService auth) =>
        {
            var body = request.ReadFromJsonAsync<Dictionary<string, string>>().Result;
            if (body == null || !body.TryGetValue("password", out var password))
                return Results.BadRequest(new { detail = "password is required" });

            var token = auth.Authenticate(password);
            return token != null
                ? Results.Ok(new { success = true, token = "desktop-session" })
                : Results.Json(new { detail = "invalid password" }, statusCode: 401);
        });
    }
}
