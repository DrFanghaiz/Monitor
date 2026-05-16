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

            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now', 'localtime'))
            );
        ";
        cmd.ExecuteNonQuery();

        MigrateRemoteSessions(conn);
        NormalizeActiveRemoteSessions(conn);
        CreateIndexes(conn);
        SetSchemaVersion(conn, "2");
    }

    private static void MigrateRemoteSessions(SqliteConnection conn)
    {
        var existing = GetExistingColumns(conn, "remote_sessions");

        AddColumnIfMissing(conn, "remote_sessions", "operator_name", "TEXT DEFAULT ''", existing);
        AddColumnIfMissing(conn, "remote_sessions", "source", "TEXT DEFAULT 'process'", existing);
        AddColumnIfMissing(conn, "remote_sessions", "end_reason", "TEXT DEFAULT ''", existing);
        AddColumnIfMissing(conn, "remote_sessions", "last_seen_at", "TEXT DEFAULT ''", existing);
    }

    private static void NormalizeActiveRemoteSessions(SqliteConnection conn)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            UPDATE remote_sessions
            SET
                end_time = datetime('now', 'localtime'),
                duration_seconds = CAST((julianday(datetime('now', 'localtime')) - julianday(start_time)) * 86400 AS INTEGER),
                is_active = 0,
                end_reason = 'deduplicated'
            WHERE is_active = 1
              AND id NOT IN (
                  SELECT id
                  FROM remote_sessions
                  WHERE is_active = 1
                  ORDER BY datetime(start_time) DESC, id DESC
                  LIMIT 1
              );
        ";
        cmd.ExecuteNonQuery();
    }

    private static void CreateIndexes(SqliteConnection conn)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            CREATE INDEX IF NOT EXISTS idx_usage_records_start_time ON usage_records(start_time);
            CREATE INDEX IF NOT EXISTS idx_usage_records_user_name ON usage_records(user_name);
            CREATE INDEX IF NOT EXISTS idx_reservations_date_status ON reservations(date, status);
            CREATE INDEX IF NOT EXISTS idx_remote_sessions_start_time ON remote_sessions(start_time);
            CREATE INDEX IF NOT EXISTS idx_remote_sessions_last_seen ON remote_sessions(last_seen_at);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_remote_sessions_one_active ON remote_sessions(is_active) WHERE is_active = 1;
        ";
        cmd.ExecuteNonQuery();
    }

    private static void SetSchemaVersion(SqliteConnection conn, string version)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO schema_meta(key, value, updated_at)
            VALUES('schema_version', @Version, datetime('now', 'localtime'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at;
        ";
        cmd.Parameters.AddWithValue("@Version", version);
        cmd.ExecuteNonQuery();
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
