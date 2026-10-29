namespace Monitor.App.Infrastructure.Security;

public class PasswordManager
{
    public static string HashPassword(string password) => BCrypt.Net.BCrypt.HashPassword(password);

    public static bool VerifyPassword(string password, string hash)
    {
        try { return BCrypt.Net.BCrypt.Verify(password, hash); }
        catch { return false; }
    }

    public static bool CheckAdminPassword(Config.AppSettings settings, string password)
    {
        var hash = settings.AdminPasswordHash;
        if (string.IsNullOrEmpty(hash))
            return password == settings.DefaultPassword;
        return VerifyPassword(password, hash);
    }

    public static void SetAdminPassword(Config.AppSettings settings, string newPassword)
    {
        settings.AdminPasswordHash = HashPassword(newPassword);
        settings.Save();
    }

    public static bool ChangeAdminPassword(Config.AppSettings settings, string oldPassword, string newPassword)
    {
        if (!CheckAdminPassword(settings, oldPassword)) return false;
        SetAdminPassword(settings, newPassword);
        return true;
    }

    public static bool IsPasswordSet(Config.AppSettings settings)
        => !string.IsNullOrEmpty(settings.AdminPasswordHash);

    public static bool CheckWebPassword(Config.AppSettings settings, string password)
    {
        if (!string.IsNullOrWhiteSpace(settings.WebServerPasswordHash))
            return VerifyPassword(password, settings.WebServerPasswordHash);

        return password == settings.WebServerPassword;
    }

    public static bool IsWebPasswordSet(Config.AppSettings settings)
        => !string.IsNullOrWhiteSpace(settings.WebServerPasswordHash);

    public static void SetWebPassword(Config.AppSettings settings, string newPassword)
    {
        settings.WebServerPasswordHash = HashPassword(newPassword.Trim());
        settings.WebServerPassword = "";
        settings.Save();
    }

    public static bool HasOperatorRegistrationKey(Config.AppSettings settings)
        => !string.IsNullOrEmpty(settings.OperatorRegistrationKeyHash);

    public static void SetOperatorRegistrationKey(Config.AppSettings settings, string key)
    {
        settings.OperatorRegistrationKeyHash = HashPassword(key.Trim());
        settings.OperatorRegistrationKey = "";
        settings.Save();
    }

    public static bool VerifyOperatorRegistrationKey(Config.AppSettings settings, string key)
    {
        if (!HasOperatorRegistrationKey(settings))
            return false;

        return VerifyPassword(key.Trim(), settings.OperatorRegistrationKeyHash);
    }
}
