using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class StatusEndpoints
{
    public static void MapStatusEndpoints(this WebApplication app)
    {
        app.MapGet("/api/status", (StatusService status) =>
        {
            var s = status.GetFullStatus();
            return Results.Ok(new
            {
                s.Timestamp,
                s.ComputerStatus,
                local_use = new
                {
                    s.LocalUse.CurrentUser,
                    s.LocalUse.StartTime,
                    s.LocalUse.ElapsedSeconds,
                    s.LocalUse.ElapsedFormatted
                },
                remote_control = new
                {
                    s.RemoteControl.IsRemote,
                    s.RemoteControl.RemoteType,
                    s.RemoteControl.StartTime,
                    s.RemoteControl.ElapsedSeconds,
                    s.RemoteControl.ElapsedFormatted
                },
                today_records = s.TodayRecords,
                today_reservations = s.TodayReservations
            });
        });
    }
}
