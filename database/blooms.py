import time

from database.connection import get_db


async def ensure_blooms_table(db) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS member_blooms (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            bloom_key TEXT NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            last_found_at INTEGER NOT NULL,

            PRIMARY KEY (
                guild_id,
                user_id,
                bloom_key
            )
        )
        """
    )

    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_member_blooms_user
        ON member_blooms (
            guild_id,
            user_id
        )
        """
    )


async def grant_bloom_in_db(
    db,
    *,
    guild_id: int,
    user_id: int,
    bloom_key: str,
    amount: int = 1,
) -> int:
    if amount <= 0:
        raise ValueError("Количество Bloom должно быть положительным")

    await ensure_blooms_table(db)

    now = int(time.time())

    await db.execute(
        """
        INSERT INTO member_blooms (
            guild_id,
            user_id,
            bloom_key,
            amount,
            last_found_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, bloom_key)
        DO UPDATE SET
            amount = member_blooms.amount + excluded.amount,
            last_found_at = excluded.last_found_at
        """,
        (
            guild_id,
            user_id,
            bloom_key,
            amount,
            now,
        ),
    )

    cursor = await db.execute(
        """
        SELECT amount
        FROM member_blooms
        WHERE guild_id = ?
          AND user_id = ?
          AND bloom_key = ?
        """,
        (
            guild_id,
            user_id,
            bloom_key,
        ),
    )

    row = await cursor.fetchone()
    await cursor.close()

    if row is None:
        raise RuntimeError("Не удалось сохранить Bloom")

    return int(row[0])


async def grant_bloom(
    guild_id: int,
    user_id: int,
    bloom_key: str,
    amount: int = 1,
) -> int:
    async with get_db() as db:
        try:
            await db.execute("BEGIN IMMEDIATE")

            total = await grant_bloom_in_db(
                db,
                guild_id=guild_id,
                user_id=user_id,
                bloom_key=bloom_key,
                amount=amount,
            )

            await db.commit()
            return total

        except Exception:
            await db.rollback()
            raise


async def get_member_blooms(
    guild_id: int,
    user_id: int,
) -> dict[str, int]:
    async with get_db() as db:
        await ensure_blooms_table(db)

        cursor = await db.execute(
            """
            SELECT bloom_key, amount
            FROM member_blooms
            WHERE guild_id = ?
              AND user_id = ?
            ORDER BY last_found_at DESC
            """,
            (
                guild_id,
                user_id,
            ),
        )

        rows = await cursor.fetchall()
        await cursor.close()
        await db.commit()

    return {
        str(row[0]): int(row[1])
        for row in rows
    }
