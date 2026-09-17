import json
import time

from dataclasses import dataclass

from database.connection import get_db


@dataclass(frozen=True)
class AuditEntry:
    audit_id: int
    guild_id: int
    actor_id: int
    action: str
    details: str | None
    created_at: int


async def ensure_audit_table(db) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            actor_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at INTEGER NOT NULL
        )
        """
    )

    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_admin_audit_guild_time
        ON admin_audit_log (
            guild_id,
            created_at DESC
        )
        """
    )


async def record_audit(
    guild_id: int,
    actor_id: int,
    action: str,
    details: dict | None = None,
) -> None:
    payload = None

    if details:
        payload = json.dumps(
            details,
            ensure_ascii=False,
            separators=(",", ":"),
        )[:2000]

    async with get_db() as db:
        await ensure_audit_table(db)

        await db.execute(
            """
            INSERT INTO admin_audit_log (
                guild_id,
                actor_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                actor_id,
                action[:120],
                payload,
                int(time.time()),
            ),
        )

        await db.commit()


async def get_recent_audit(
    guild_id: int,
    limit: int = 15,
) -> list[AuditEntry]:
    safe_limit = max(1, min(limit, 50))

    async with get_db() as db:
        await ensure_audit_table(db)

        cursor = await db.execute(
            """
            SELECT
                audit_id,
                guild_id,
                actor_id,
                action,
                details,
                created_at
            FROM admin_audit_log
            WHERE guild_id = ?
            ORDER BY audit_id DESC
            LIMIT ?
            """,
            (
                guild_id,
                safe_limit,
            ),
        )

        rows = await cursor.fetchall()
        await cursor.close()
        await db.commit()

    return [
        AuditEntry(
            audit_id=int(row[0]),
            guild_id=int(row[1]),
            actor_id=int(row[2]),
            action=str(row[3]),
            details=(str(row[4]) if row[4] is not None else None),
            created_at=int(row[5]),
        )
        for row in rows
    ]
