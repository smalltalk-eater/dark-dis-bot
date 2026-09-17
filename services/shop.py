import time

from dataclasses import dataclass

from config.economy import (
    REASON_SHOP,
    SHOP_CASE_PRICE,
    SHOP_MAX_CASES_PER_PURCHASE,
)
from database.connection import get_db


@dataclass(frozen=True)
class CasePurchaseResult:
    status: str
    amount: int
    total_cost: int
    new_balance: int | None = None
    new_cases: int | None = None


async def buy_eden_cases(
    guild_id: int,
    user_id: int,
    amount: int,
) -> CasePurchaseResult:
    if amount < 1 or amount > SHOP_MAX_CASES_PER_PURCHASE:
        return CasePurchaseResult(
            status="invalid_amount",
            amount=amount,
            total_cost=0,
        )

    total_cost = SHOP_CASE_PRICE * amount

    async with get_db() as db:
        try:
            await db.execute("BEGIN IMMEDIATE")

            await db.execute(
                """
                INSERT OR IGNORE INTO member_stats (
                    guild_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    guild_id,
                    user_id,
                ),
            )

            cursor = await db.execute(
                """
                SELECT currency, eden_cases
                FROM member_stats
                WHERE guild_id = ?
                  AND user_id = ?
                """,
                (
                    guild_id,
                    user_id,
                ),
            )

            row = await cursor.fetchone()
            await cursor.close()

            if row is None:
                raise RuntimeError("Не удалось получить данные магазина")

            balance = int(row[0])
            cases = int(row[1])

            if balance < total_cost:
                await db.rollback()

                return CasePurchaseResult(
                    status="insufficient_funds",
                    amount=amount,
                    total_cost=total_cost,
                    new_balance=balance,
                    new_cases=cases,
                )

            new_balance = balance - total_cost
            new_cases = cases + amount

            await db.execute(
                """
                UPDATE member_stats
                SET
                    currency = ?,
                    eden_cases = ?
                WHERE guild_id = ?
                  AND user_id = ?
                """,
                (
                    new_balance,
                    new_cases,
                    guild_id,
                    user_id,
                ),
            )

            await db.execute(
                """
                INSERT INTO currency_transactions (
                    guild_id,
                    user_id,
                    amount,
                    reason,
                    description,
                    actor_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    user_id,
                    -total_cost,
                    REASON_SHOP,
                    f"eden_case_x{amount}",
                    user_id,
                    int(time.time()),
                ),
            )

            await db.commit()

            return CasePurchaseResult(
                status="purchased",
                amount=amount,
                total_cost=total_cost,
                new_balance=new_balance,
                new_cases=new_cases,
            )

        except Exception:
            await db.rollback()
            raise
