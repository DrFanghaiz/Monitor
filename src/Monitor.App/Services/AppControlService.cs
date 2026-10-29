namespace Monitor.App.Services;

public sealed class AppControlService
{
    public Func<Task>? FactoryResetHandler { get; set; }

    public Task FactoryResetAsync()
        => FactoryResetHandler?.Invoke() ?? Task.CompletedTask;
}
