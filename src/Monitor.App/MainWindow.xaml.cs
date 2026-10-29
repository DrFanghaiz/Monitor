using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using Microsoft.AspNetCore.Components.WebView.Wpf;
using Monitor.App.Models;

namespace Monitor.App;

public partial class MainWindow : Window
{
    private const int WM_QUERYENDSESSION = 0x0011;

    public MainWindow()
    {
        InitializeComponent();
        WebView.RootComponents.Add(new RootComponent
        {
            Selector = "#app",
            ComponentType = typeof(Monitor.App.Components.App)
        });
    }

    protected override void OnSourceInitialized(EventArgs e)
    {
        base.OnSourceInitialized(e);
        if (PresentationSource.FromVisual(this) is HwndSource source)
            source.AddHook(WndProc);
    }

    /// <summary>
    /// 关机/注销保护：收到 WM_QUERYENDSESSION 时，若检测到计算任务正在运行，
    /// 弹出二次确认；用户选择"否"则阻止本次关机。
    /// </summary>
    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg != WM_QUERYENDSESSION)
            return IntPtr.Zero;

        if (!App.ShutdownGuardEnabled)
            return IntPtr.Zero;

        var svc = App.ComputeMonitorService;
        if (svc == null)
            return IntPtr.Zero;

        ComputeInfo status;
        try { status = svc.Sample(); }
        catch { status = svc.GetStatus(); }

        var last = svc.GetStatus();
        bool busy = status.IsBusy || last.IsBusy;
        if (!busy)
            return IntPtr.Zero;

        int count = Math.Max(status.ProcessCount, last.ProcessCount);
        string detail = count > 0
            ? $"检测到 {count} 个计算任务正在运行"
            : "检测到整机 CPU 高负载，可能有计算任务正在运行";

        string reason = $"{detail}。现在关机/重启会中断计算，可能丢失结果。";
        try { ShutdownBlockReasonCreate(hwnd, reason); } catch { }

        var choice = MessageBox.Show(
            this,
            $"{reason}\n\n确定仍要关机吗？",
            "有计算任务正在运行",
            MessageBoxButton.YesNo,
            MessageBoxImage.Warning,
            MessageBoxResult.No);

        if (choice != MessageBoxResult.Yes)
        {
            // 阻止关机
            handled = true;
            return IntPtr.Zero; // FALSE
        }

        try { ShutdownBlockReasonDestroy(hwnd); } catch { }
        return IntPtr.Zero;
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool ShutdownBlockReasonCreate(IntPtr hWnd, string pwszReason);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool ShutdownBlockReasonDestroy(IntPtr hWnd);
}
