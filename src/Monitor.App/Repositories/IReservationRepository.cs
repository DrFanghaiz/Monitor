using Monitor.App.Models;

namespace Monitor.App.Repositories;

public interface IReservationRepository
{
    int AddReservation(string userName, string date, int startHour, int endHour);
    List<Reservation> GetReservations(string? date = null);
    bool CheckReservationConflict(string date, int startHour, int endHour, int? excludeId = null);
    void CancelReservation(int id);
    List<Reservation> GetTodayReservations(string todayStr);
}
