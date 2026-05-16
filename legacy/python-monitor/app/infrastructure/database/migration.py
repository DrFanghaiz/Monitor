"""
Legacy data migration: imports usage records from old usage_history.txt file.
"""
from pathlib import Path
from app.infrastructure.database.connection import ConnectionManager


def migrate_from_txt(conn_mgr: ConnectionManager, txt_path: Path):
    """
    Migrate data from legacy usage_history.txt to the database.
    Skips if file doesn't exist or database already has records.
    """
    if not txt_path.exists():
        return

    # Check if database already has data
    with conn_mgr.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_records")
        if cursor.fetchone()[0] > 0:
            return

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        records = []
        for line in lines:
            if "|" not in line:
                continue
            parts = line.strip().split("|")
            if len(parts) >= 4:
                user_name, start_str, end_str, dur_str = parts[:4]
                h, m, s = 0, 0, 0
                temp = dur_str
                if "小时" in temp:
                    h, temp = int(temp.split("小时")[0]), temp.split("小时")[1]
                if "分" in temp:
                    m, temp = int(temp.split("分")[0]), temp.split("分")[1]
                if "秒" in temp:
                    s = int(temp.split("秒")[0])
                duration_seconds = h * 3600 + m * 60 + s
                records.append((user_name, start_str, end_str, duration_seconds))

        if records:
            with conn_mgr.connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT INTO usage_records (user_name, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?)",
                    records
                )
                conn.commit()
                cursor.execute(
                    "INSERT INTO audit_log (action, details) VALUES (?, ?)",
                    ("data_migration", f"从 txt 迁移了 {len(records)} 条记录")
                )
                conn.commit()

            backup_name = txt_path.with_suffix(".txt.bak")
            txt_path.rename(backup_name)

    except Exception as e:
        print(f"数据迁移失败: {e}")
