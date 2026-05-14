using Microsoft.Data.Sqlite;
using Serilog;

namespace Monitor.App.Infrastructure.Database;

public class SchemaInitializer
{
    public static void Initialize(DbConnectionFactory factory)
    {
        using var conn = factory.CreateConnection();
        using var cmd = conn.CreateCommand();

        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                date TEXT NOT NULL,
                start_hour INTEGER NOT NULL,
                end_hour INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS remote_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remote_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ";
        cmd.ExecuteNonQuery();

        // Phase 2: add new columns to remote_sessions (safe migration)
        MigrateRemoteSessions(conn);
    }

    private static void MigrateRemoteSessions(SqliteConnection conn)
    {
        var existing = GetExistingColumns(conn, "remote_sessions");

        AddColumnIfMissing(conn, "remote_sessions", "operator_name", "TEXT DEFAULT ''", existing);
        AddColumnIfMissing(conn, "remote_sessions", "source", "TEXT DEFAULT 'process'", existing);
        AddColumnIfMissing(conn, "remote_sessions", "end_reason", "TEXT DEFAULT ''", existing);
        AddColumnIfMissing(conn, "remote_sessions", "last_seen_at", "TEXT DEFAULT ''", existing);
    }

    private static HashSet<string> GetExistingColumns(SqliteConnection conn, string table)
    {
        var columns = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $"PRAGMA table_info({table})";
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            columns.Add(reader.GetString(reader.GetOrdinal("name")));
        }
        return columns;
    }

    private static void AddColumnIfMissing(SqliteConnection conn, string table,
        string column, string type, HashSet<string> existing)
    {
        if (existing.Contains(column))
        {
            Log.Debug("Column {Column} already exists in {Table}, skipping", column, table);
            return;
        }

        try
        {
            using var cmd = conn.CreateCommand();
            cmd.CommandText = $"ALTER TABLE {table} ADD COLUMN {column} {type}";
            cmd.ExecuteNonQuery();
            Log.Information("Added column {Column} to {Table}", column, table);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to add column {Column} to {Table}", column, table);
            throw;
        }
    }
}
