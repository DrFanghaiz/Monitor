namespace Monitor.App.Services;

/// <summary>
/// Tracks the web server health for StatusService and Settings UI.
/// </summary>
public class WebServerInfo
{
    public bool Enabled { get; set; }
    public int Port { get; set; }
    public string? Error { get; set; }
    public string? PublicUrl { get; set; }
}
