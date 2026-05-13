namespace Monitor.App.Infrastructure.System;

public class InstanceLock : IDisposable
{
    private Mutex? _mutex;
    private bool _owned;

    public bool Acquire()
    {
        _mutex = new Mutex(true, @"Global\MonitorApp_Instance", out _owned);
        return _owned;
    }

    public void Release()
    {
        if (_owned && _mutex != null)
        {
            _mutex.ReleaseMutex();
            _owned = false;
        }
    }

    public void Dispose()
    {
        Release();
        _mutex?.Dispose();
    }
}
