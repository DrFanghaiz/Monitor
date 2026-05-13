using Dapper;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Models;

namespace Monitor.App.Repositories;

public class ReservationRepository : IReservationRepository
{
    private readonly DbConnectionFactory _factory;

    public ReservationRepository(DbConnectionFactory factory) => _factory = factory;

    public int AddReservation(string userName, string date, int startHour, int endHour)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"INSERT INTO reservations (user_name, date, start_hour, end_hour)
                    VALUES (@Name, @Date, @Start, @End); SELECT last_insert_rowid();";
        return conn.ExecuteScalar<int>(sql, new { Name = userName, Date = date, Start = startHour, End = endHour });
    }

    public List<Reservation> GetReservations(string? date = null)
    {
        using var conn = _factory.CreateConnection();
        var sql = "SELECT id AS Id, user_name AS UserName, date AS Date, start_hour AS StartHour, end_hour AS EndHour, created_at AS CreatedAt, status AS Status FROM reservations WHERE status = 'active'";
        if (date != null)
            sql += " AND date = @Date";
        sql += " ORDER BY start_hour";
        return conn.Query<Reservation>(sql, new { Date = date }).AsList();
    }

    public bool CheckReservationConflict(string date, int startHour, int endHour, int? excludeId = null)
    {
        using var conn = _factory.CreateConnection();
        var sql = @"SELECT COUNT(*) FROM reservations
                    WHERE status = 'active' AND date = @Date
                    AND ((start_hour < @End AND end_hour > @Start))";
        var parameters = new Dictionary<string, object>
        {
            { "Date", date }, { "Start", startHour }, { "End", endHour }
        };
        if (excludeId.HasValue)
        {
            sql += " AND id != @ExcludeId";
            parameters["ExcludeId"] = excludeId.Value;
        }
        return conn.ExecuteScalar<int>(sql, parameters) > 0;
    }

    public void CancelReservation(int id)
    {
        using var conn = _factory.CreateConnection();
        conn.Execute("UPDATE reservations SET status = 'cancelled' WHERE id = @Id", new { Id = id });
    }

    public List<Reservation> GetTodayReservations(string todayStr) => GetReservations(todayStr);
}
