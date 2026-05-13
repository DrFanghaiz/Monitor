using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class StatisticsEndpoints
{
    public static void MapStatisticsEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/statistics");

        group.MapGet("/users", (StatisticsService svc, string? filter_mode) =>
        {
            var users = svc.GetUserStats(filter_mode ?? "all");
            return Results.Ok(new { users });
        });

        group.MapGet("/hourly", (StatisticsService svc) =>
        {
            var hourly = svc.GetHourlyStats();
            return Results.Ok(new { hourly });
        });

        group.MapGet("/daily", (StatisticsService svc, int? days) =>
        {
            var daily = svc.GetDailyStats(days ?? 30);
            return Results.Ok(new { daily });
        });

        group.MapGet("/distribution", (StatisticsService svc, string? filter_mode) =>
        {
            var dist = svc.GetUserDistribution(filter_mode ?? "all");
            return Results.Ok(new { distribution = dist });
        });
    }
}
