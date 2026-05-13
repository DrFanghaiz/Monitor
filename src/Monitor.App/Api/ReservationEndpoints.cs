using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Monitor.App.Services;

namespace Monitor.App.Api;

public static class ReservationEndpoints
{
    public static void MapReservationEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/reservations");

        group.MapGet("/", (ReservationService svc, string? date) =>
        {
            var list = svc.GetReservations(date);
            return Results.Ok(new { reservations = list });
        });

        group.MapPost("/", (ReservationCreateRequest req, ReservationService svc) =>
        {
            var (success, message, id) = svc.CreateReservation(req.UserName, req.Date, req.StartHour, req.EndHour);
            if (success)
                return Results.Ok(new { success = true, message, id });
            return Results.Json(new { detail = message }, statusCode: 409);
        });

        group.MapPost("/{id:int}/cancel", (int id, ReservationService svc) =>
        {
            svc.CancelReservation(id);
            return Results.Ok(new { success = true });
        });
    }
}

public record ReservationCreateRequest(string UserName, string Date, int StartHour, int EndHour);
