import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


class SqliteCache:
    def __init__(self, cache_file: Path) -> None:
        self._db = sqlite3.connect(cache_file)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL,
                content TEXT NOT NULL
            )
        """)

    def get_cached(self, id) -> str | None:
        """Fetches the content from the cache if it exists, otherwise None"""
        row = self._db.execute(
            "SELECT content FROM cache WHERE id = ?", (id,)
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def set_cached(self, id: str, content: str) -> None:
        """Sets cache for the id at the current time"""
        self._db.execute(
            """
            INSERT OR REPLACE INTO cache (id, created_at, content)
            VALUES (?, ?, ?)
            """,
            (id, int(datetime.now(timezone.utc).timestamp()), content),
        )
        self._db.commit()

    def clear_before(self, before: datetime) -> None:
        timestamp = int(before.timestamp())
        self._db.execute("DELETE FROM cache WHERE created_at < ?", (timestamp,))
        self._db.commit()

    def clear_older_than(self, delta: timedelta) -> None:
        self.clear_before(datetime.now(timezone.utc) - delta)

    def clear_cache(self) -> None:
        pass
