using Monitor.App.Models;

namespace Monitor.App.Repositories;

public interface IUsageRepository
{
    int AddUsageRecord(string userName, string startTime, string endTime);
    List<UseHistoryItem> GetUsageRecords(string filterMode = "all");
    List<UseHistoryItem> GetTodayRecords();
    List<UserStat> GetUserStats(string filterMode = "all");
    void DeleteUsageRecord(int id);
    void DeleteUsageRecords(List<int> ids);
    List<HourlyStat> GetHourlyStats();
    List<DailyStat> GetDailyStats(int days = 30);
    List<UserStat> GetUserDistribution(string filterMode = "all");
}
