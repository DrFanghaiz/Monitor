using System.Windows;
using Microsoft.AspNetCore.Components.WebView.Wpf;

namespace Monitor.App;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        WebView.RootComponents.Add(new RootComponent
        {
            Selector = "#app",
            ComponentType = typeof(Monitor.App.Components.App)
        });
    }
}
