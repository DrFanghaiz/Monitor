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
}
