using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class TimerEndpoints
{
    public static void MapTimerEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/timer");

        group.MapPost("/start", (TimerStartRequest req, TimerService svc) =>
        {
            if (svc.StartTimer(req.UserName))
                return Results.Ok(new { success = true, message = "started" });
            return Results.BadRequest(new { detail = "user_name is required" });
        });

        group.MapPost("/stop", (TimerService svc) =>
        {
            var r = svc.StopTimer();
            return r != null
                ? Results.Ok(new { r.Success, r.UserName, r.DurationSeconds, r.DurationFormatted, r.ElapsedFormatted })
                : Results.BadRequest(new { detail = "timer not running" });
        });

        group.MapGet("/state", (TimerService svc) =>
        {
            var s = svc.GetState();
            return Results.Ok(new
            {
                s.IsRunning,
                s.CurrentUser,
                s.StartTime,
                s.ElapsedSeconds,
                s.ElapsedFormatted
            });
        });

        group.MapGet("/history", (TimerService svc, string? filter_mode, string? search) =>
        {
            var records = svc.GetHistory(filter_mode ?? "all", search ?? "");
            return Results.Ok(new { records });
        });

        group.MapDelete("/history/{id:int}", (int id, TimerService svc) =>
        {
            svc.DeleteRecord(id);
            return Results.Ok(new { success = true });
        });

        group.MapPost("/history/delete-batch", (DeleteBatchRequest req, TimerService svc) =>
        {
            var deleted = svc.DeleteRecords(req.Ids);
            return Results.Ok(new { success = true, deleted });
        });
    }
}

public record TimerStartRequest(string UserName);
public record DeleteBatchRequest(List<int> Ids);
