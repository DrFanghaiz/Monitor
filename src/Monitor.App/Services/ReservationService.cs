using Monitor.App.Models;
using Monitor.App.Repositories;

namespace Monitor.App.Services;

public class ReservationService
{
    private readonly IReservationRepository _repo;
    private readonly IAuditRepository _auditRepo;

    public ReservationService(IReservationRepository repo, IAuditRepository auditRepo)
    {
        _repo = repo;
        _auditRepo = auditRepo;
    }

    public List<Reservation> GetReservations(string? date = null) => _repo.GetReservations(date);

    public (bool Success, string Message, int? Id) CreateReservation(string userName, string date, int startHour, int endHour)
    {
        if (string.IsNullOrWhiteSpace(userName))
            return (false, "姓名不能为空", null);

        if (endHour <= startHour)
            return (false, "结束时间必须大于开始时间", null);

        if (_repo.CheckReservationConflict(date, startHour, endHour))
            return (false, "该时间段已被预约", null);

        var id = _repo.AddReservation(userName.Trim(), date, startHour, endHour);
        _auditRepo.LogAction("reservation_added", $"user={userName},date={date},{startHour}-{endHour}");
        return (true, "预约成功", id);
    }

    public void CancelReservation(int id)
    {
        _repo.CancelReservation(id);
        _auditRepo.LogAction("reservation_cancelled", $"id={id}");
    }

    public bool CheckConflict(string date, int startHour, int endHour, int? excludeId = null)
        => _repo.CheckReservationConflict(date, startHour, endHour, excludeId);

    public List<Reservation> GetTodayReservations(string todayStr) => _repo.GetTodayReservations(todayStr);
}
