using System.Collections.Concurrent;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

namespace Monitor.App.Api;

public static class WindowEndpoints
{
    private static readonly ConcurrentQueue<string> _actions = new();
    private static readonly string _desktopToken = Guid.NewGuid().ToString("N");

    public static string DesktopToken => _desktopToken;

    public static bool TryDequeue(out string action) => _actions.TryDequeue(out action!);

    public static void MapWindowEndpoints(this WebApplication app)
    {
        app.MapPost("/api/window/minimize", (string token) => EnqueueIfValid(token, "minimize"));
        app.MapPost("/api/window/maximize", (string token) => EnqueueIfValid(token, "maximize"));
        app.MapPost("/api/window/close", (string token) => EnqueueIfValid(token, "close"));
        app.MapPost("/api/window/toggle-maximize", (string token) => EnqueueIfValid(token, "toggle_maximize"));
        app.MapPost("/api/window/drag", (string token) => EnqueueIfValid(token, "drag"));
        app.MapGet("/api/window/mode", (string token) =>
            Results.Ok(new { desktop = token == _desktopToken }));
    }

    private static IResult EnqueueIfValid(string token, string action)
    {
        if (token != _desktopToken)
            return Results.Json(new { detail = "forbidden" }, statusCode: 403);
        _actions.Enqueue(action);
        return Results.Ok(new { ok = true });
    }
}
