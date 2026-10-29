using System.Windows;
using System.Diagnostics;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Data.Sqlite;
using Monitor.App.Api;
using Monitor.App.Infrastructure.Config;
using Monitor.App.Infrastructure.Database;
using Monitor.App.Repositories;
using Monitor.App.Services;
using Serilog;

namespace Monitor.App;

public partial class App : Application
{
    private ServiceProvider? _services;
    private CancellationTokenSource? _webCts;
    private RemoteMonitorService? _remoteMonitorService;
    private ComputeMonitorService? _computeMonitorService;
    private TunnelService? _tunnelService;
    private AppControlService? _appControlService;
    private bool _resetInProgress;

    /// <summary>供 MainWindow（关机保护）访问的当前计算监控服务。</summary>
    public static ComputeMonitorService? ComputeMonitorService { get; private set; }

    /// <summary>是否启用关机/注销保护（来自配置）。</summary>
    public static bool ShutdownGuardEnabled { get; private set; } = true;

    private void Application_Startup(object sender, StartupEventArgs e)
    {
        AppPaths.EnsureDataDirectory();
        var dbPath = AppPaths.DatabasePath;
        var configPath = AppPaths.ConfigPath;

        // ---- Config ----
        var settings = AppSettings.Load();
        ShutdownGuardEnabled = settings.ShutdownGuardEnabled;

        // ---- Logging ----
        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Debug()
            .WriteTo.Console()
            .WriteTo.File(AppPaths.LogPath,
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
        var computeMonitorService = new ComputeMonitorService(settings);
        var tunnelService = new TunnelService(settings);
        var statusService = new StatusService(timerService, remoteMonitorService, computeMonitorService, usageRepo, reservationRepo);
        var webAccessService = new WebAccessService(settings);
        var backupService = new BackupService(settings, dbPath, configPath);
        var webServerInfo = new WebServerInfo();
        var appControlService = new AppControlService();

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
        sc.AddSingleton(computeMonitorService);
        sc.AddSingleton(tunnelService);
        sc.AddSingleton(webServerInfo);
        sc.AddSingleton(appControlService);

        _services = sc.BuildServiceProvider();
        Resources.Add("services", _services);
        _remoteMonitorService = remoteMonitorService;
        _computeMonitorService = computeMonitorService;
        ComputeMonitorService = computeMonitorService;
        _tunnelService = tunnelService;
        _appControlService = appControlService;
        _appControlService.FactoryResetHandler = ResetToFactoryAsync;

        // ---- Background tasks ----
        try { backupService.AutoBackupIfNeeded(); }
        catch (Exception ex) { Log.Warning(ex, "Auto backup skipped"); }
        _ = remoteMonitorService.StartAsync(CancellationToken.None);
        computeMonitorService.StartAsync(CancellationToken.None);
        _ = tunnelService.StartAsync(CancellationToken.None);

        // ---- Web API ----
        if (settings.WebServerEnabled)
        {
            StartWebHost(settings, sc, webServerInfo);
        }
        else
        {
            webServerInfo.Enabled = false;
            webServerInfo.Error = "Web 发布未开启";
            Log.Information("Web server not started (disabled in config)");
        }

        // ---- Show window ----
        var window = new MainWindow();
        window.Closed += (_, _) =>
        {
            _webCts?.Cancel();
            remoteMonitorService.Dispose();
            computeMonitorService.Dispose();
            tunnelService.Dispose();
            _services?.Dispose();
            Log.CloseAndFlush();
            Shutdown();
        };
        window.Show();
    }

    private async Task ResetToFactoryAsync()
    {
        if (_resetInProgress)
            return;

        _resetInProgress = true;
        Log.Information("Factory reset requested");

        try
        {
            _webCts?.Cancel();

            if (_remoteMonitorService != null)
                await _remoteMonitorService.StopAsync(CancellationToken.None);

            _tunnelService?.Dispose();
            SqliteConnection.ClearAllPools();

            TryDeleteFile(AppPaths.ConfigPath);
            TryDeleteFile(AppPaths.DatabasePath);
            TryDeleteDirectory(AppPaths.BackupDirectory);

            Directory.CreateDirectory(AppPaths.DataDirectory);
            Directory.CreateDirectory(AppPaths.BackupDirectory);
            Directory.CreateDirectory(AppPaths.LogDirectory);

            var exePath = Environment.ProcessPath ?? Process.GetCurrentProcess().MainModule?.FileName;
            if (!string.IsNullOrWhiteSpace(exePath))
            {
                Process.Start(new ProcessStartInfo(exePath)
                {
                    UseShellExecute = true,
                    WorkingDirectory = Path.GetDirectoryName(exePath)!
                });
            }

            Shutdown();
        }
        catch (Exception ex)
        {
            _resetInProgress = false;
            Log.Error(ex, "Factory reset failed");
            throw;
        }
    }

    private static void TryDeleteFile(string path)
    {
        if (File.Exists(path))
            File.Delete(path);
    }

    private static void TryDeleteDirectory(string path)
    {
        if (Directory.Exists(path))
            Directory.Delete(path, recursive: true);
    }

    private void StartWebHost(AppSettings settings, ServiceCollection sc, WebServerInfo webServerInfo)
    {
        _webCts = new CancellationTokenSource();

        Task.Run(() =>
        {
            try
            {
                var builder = WebApplication.CreateBuilder();
                builder.WebHost.UseUrls($"http://127.0.0.1:{settings.WebServerPort}");
                builder.Host.UseSerilog();

                foreach (var sd in sc)
                    builder.Services.Add(sd);

                builder.Services.AddCors();
                builder.Services.ConfigureHttpJsonOptions(opts =>
                {
                    opts.SerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.SnakeCaseLower;
                });

                var app = builder.Build();
                app.UseCors(c => c.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());

                app.MapAuthEndpoints();
                app.MapStatusEndpoints();
                app.MapTimerEndpoints();
                app.MapStatisticsEndpoints();
                app.MapReservationEndpoints();
                app.MapSettingsEndpoints();
                app.MapWebStatusPages();
                app.MapRemoteEndpoints();

                webServerInfo.Enabled = true;
                webServerInfo.Port = settings.WebServerPort;
                webServerInfo.Error = null;
                Log.Information("Web API listening on http://127.0.0.1:{Port}", settings.WebServerPort);

                app.RunAsync(_webCts.Token).GetAwaiter().GetResult();
            }
            catch (OperationCanceledException) { }
            catch (Exception ex)
            {
                webServerInfo.Enabled = true;
                webServerInfo.Port = settings.WebServerPort;
                webServerInfo.Error = $"Web 服务启动失败: {ex.Message}";
                Log.Error(ex, "Web API failed to start on port {Port}", settings.WebServerPort);
            }
        }, _webCts.Token);
    }
}
