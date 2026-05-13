using Monitor.App.Repositories;

namespace Monitor.App.Services;

public class StatisticsService
{
    private readonly IUsageRepository _usageRepo;

    public StatisticsService(IUsageRepository usageRepo) => _usageRepo = usageRepo;

    public object GetUserStats(string filterMode = "all") => _usageRepo.GetUserStats(filterMode);
    public object GetHourlyStats() => _usageRepo.GetHourlyStats();
    public object GetDailyStats(int days = 30) => _usageRepo.GetDailyStats(days);
    public object GetUserDistribution(string filterMode = "all") => _usageRepo.GetUserDistribution(filterMode);
}
