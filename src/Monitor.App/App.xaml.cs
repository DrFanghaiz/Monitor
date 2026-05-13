using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Monitor.App.Infrastructure.Config;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Repositories;
using Monitor.App.Services;
using Serilog;

namespace Monitor.App;

public partial class App : Application
{
    private ServiceProvider? _services;

    private void Application_Startup(object sender, StartupEventArgs e)
    {
        var baseDir = AppDomain.CurrentDomain.BaseDirectory;
        var dbPath = Path.Combine(baseDir, "monitor.db");
        var configPath = Path.Combine(baseDir, "config.json");

        // ---- Config ----
        var settings = AppSettings.Load();

        // ---- Logging ----
        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Debug()
            .WriteTo.Console()
            .WriteTo.File(Path.Combine(baseDir, "app.log"),
                rollingInterval: RollingInterval.Day,
                fileSizeLimitBytes: 5 * 1024 * 1024,
                retainedFileCountLimit: 3,
                outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss} | {Level:u} | {Message}{NewLine}{Exception}")
            .CreateLogger();

        // ---- Database ----
        var dbFactory = new DbConnectionFactory(dbPath);
        SchemaInitializer.Initialize(dbFactory);

        // ---- Repositories ----
        var usageRepo = new UsageRepository(dbFactory);
        var reservationRepo = new ReservationRepository(dbFactory);
        var remoteSessionRepo = new RemoteSessionRepository(dbFactory);
        var auditRepo = new AuditRepository(dbFactory);

        // ---- Services ----
        var timerService = new TimerService(usageRepo, auditRepo);
        var reservationService = new ReservationService(reservationRepo, auditRepo);
        var statisticsService = new StatisticsService(usageRepo);
        var remoteMonitorService = new RemoteMonitorService(settings, remoteSessionRepo);
        var tunnelService = new TunnelService(settings);
        var statusService = new StatusService(timerService, remoteMonitorService, usageRepo, reservationRepo);
        var webAccessService = new WebAccessService(settings);
        var backupService = new BackupService(settings, dbPath, configPath);

        // ---- DI Container ----
        var sc = new ServiceCollection();
        sc.AddWpfBlazorWebView();
#if DEBUG
        sc.AddBlazorWebViewDeveloperTools();
#endif

        sc.AddSingleton(settings);
        sc.AddSingleton(dbFactory);

        sc.AddSingleton<IUsageRepository>(usageRepo);
        sc.AddSingleton<IReservationRepository>(reservationRepo);
        sc.AddSingleton<IRemoteSessionRepository>(remoteSessionRepo);
        sc.AddSingleton<IAuditRepository>(auditRepo);

        sc.AddSingleton(timerService);
        sc.AddSingleton(reservationService);
        sc.AddSingleton(statisticsService);
        sc.AddSingleton(statusService);
        sc.AddSingleton(webAccessService);
        sc.AddSingleton(backupService);
        sc.AddSingleton(remoteMonitorService);
        sc.AddSingleton(tunnelService);

        _services = sc.BuildServiceProvider();
        Resources.Add("services", _services);

        // ---- Background tasks ----
        try { backupService.AutoBackupIfNeeded(); }
        catch (Exception ex) { Log.Warning(ex, "Auto backup skipped"); }
        _ = remoteMonitorService.StartAsync(CancellationToken.None);
        _ = tunnelService.StartAsync(CancellationToken.None);

        // ---- Show window ----
        var window = new MainWindow();
        window.Closed += (_, _) =>
        {
            remoteMonitorService.Dispose();
            tunnelService.Dispose();
            _services?.Dispose();
            Log.CloseAndFlush();
            Shutdown();
        };
        window.Show();
    }
}
