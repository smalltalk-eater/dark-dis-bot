import pytest

from config.blooms import BLOOMS
from database.connection import get_db
from services.blooms import add_bloom, get_bloom_collection
from services.cases import CaseReward, open_eden_case


@pytest.mark.asyncio
async def test_bloom_collection_accumulates(test_db):
    guild_id = 710
    user_id = 81

    first = await add_bloom(
        guild_id=guild_id,
        user_id=user_id,
        bloom_key="pale_bloom",
    )
    second = await add_bloom(
        guild_id=guild_id,
        user_id=user_id,
        bloom_key="pale_bloom",
        amount=2,
    )

    collection = await get_bloom_collection(
        guild_id=guild_id,
        user_id=user_id,
    )

    assert first == 1
    assert second == 3
    assert collection["pale_bloom"] == 3
    assert collection["lost_bloom"] == 0


@pytest.mark.asyncio
async def test_case_can_grant_bonus_bloom(test_db, monkeypatch):
    guild_id = 711
    user_id = 82

    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO member_stats (
                guild_id,
                user_id,
                eden_cases
            )
            VALUES (?, ?, 1)
            """,
            (guild_id, user_id),
        )
        await db.commit()

    reward = CaseReward(
        kind="currency",
        amount=15,
        weight=1,
        title="15 test",
        rarity="COMMON",
    )

    monkeypatch.setattr(
        "services.cases.roll_case_reward",
        lambda: reward,
    )
    monkeypatch.setattr(
        "services.cases.roll_case_bloom",
        lambda: BLOOMS["moon_bloom"],
    )

    result = await open_eden_case(
        guild_id=guild_id,
        user_id=user_id,
    )

    collection = await get_bloom_collection(
        guild_id=guild_id,
        user_id=user_id,
    )

    assert result is not None
    assert result.bloom == BLOOMS["moon_bloom"]
    assert collection["moon_bloom"] == 1
