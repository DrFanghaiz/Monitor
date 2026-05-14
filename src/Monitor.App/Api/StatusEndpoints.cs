using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class StatusEndpoints
{
    public static void MapStatusEndpoints(this WebApplication app)
    {
        app.MapGet("/api/status", (StatusService status, WebServerInfo webInfo) =>
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
                    s.RemoteControl.ElapsedFormatted,
                    s.RemoteControl.Status,
                    s.RemoteControl.Source,
                    s.RemoteControl.Confidence,
                    s.RemoteControl.OperatorName,
                    s.RemoteControl.LastSeenAt,
                    s.RemoteControl.ErrorMessage,
                    s.RemoteControl.MatchedSignals,
                    s.RemoteControl.Message
                },
                today_records = s.TodayRecords,
                today_reservations = s.TodayReservations,
                web_server = new
                {
                    enabled = webInfo.Enabled,
                    port = webInfo.Port,
                    error = webInfo.Error,
                    public_url = webInfo.PublicUrl
                }
            });
        });
    }
}
