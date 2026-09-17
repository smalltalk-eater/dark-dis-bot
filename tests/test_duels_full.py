import time

import pytest

from database.connection import get_db
from database.member_stats import get_member_stats
from services.activities import change_activity_status
from services.automatic_activity_rewards import (
    reward_duel_winner_automatically,
)
from services.duels import (
    confirm_duel_result,
    create_duel,
    get_duel_result,
    propose_duel_result,
)


@pytest.mark.asyncio
async def test_duel_full_confirmed_reward_flow(test_db):
    guild_id = 730
    challenger_id = 101
    opponent_id = 102

    created = await create_duel(
        guild_id=guild_id,
        challenger_id=challenger_id,
        opponent_id=opponent_id,
        title="Full duel",
    )

    assert created.status == "created"
    assert created.activity is not None

    activity_id = created.activity.activity_id

    status, _ = await change_activity_status(
        guild_id=guild_id,
        activity_id=activity_id,
        new_status="running",
    )
    assert status == "changed"

    async with get_db() as db:
        await db.execute(
            """
            UPDATE activities
            SET starts_at = ?
            WHERE activity_id = ?
            """,
            (
                int(time.time()) - 180,
                activity_id,
            ),
        )
        await db.commit()

    result_status, pending = await propose_duel_result(
        guild_id=guild_id,
        activity_id=activity_id,
        winner_id=challenger_id,
        submitted_by=challenger_id,
    )

    assert result_status == "created"
    assert pending is not None
    assert pending.status == "pending"

    confirm_status, activity = await confirm_duel_result(
        guild_id=guild_id,
        activity_id=activity_id,
        confirmed_by=opponent_id,
    )

    assert confirm_status == "confirmed"
    assert activity is not None
    assert activity.status == "finished"

    rewards = await reward_duel_winner_automatically(
        guild_id=guild_id,
        activity_id=activity_id,
        winner_id=challenger_id,
        actor_id=opponent_id,
    )

    winner = await get_member_stats(
        guild_id=guild_id,
        user_id=challenger_id,
    )
    loser = await get_member_stats(
        guild_id=guild_id,
        user_id=opponent_id,
    )

    assert {item.status for item in rewards} == {"granted"}
    assert winner.xp == 5
    assert winner.currency == 8
    assert loser.xp == 0
    assert loser.currency == 0

    second_rewards = await reward_duel_winner_automatically(
        guild_id=guild_id,
        activity_id=activity_id,
        winner_id=challenger_id,
        actor_id=opponent_id,
    )

    winner_after = await get_member_stats(
        guild_id=guild_id,
        user_id=challenger_id,
    )

    assert {item.status for item in second_rewards} == {"already_granted"}
    assert winner_after.xp == 5
    assert winner_after.currency == 8

    stored_result = await get_duel_result(activity_id)
    assert stored_result is not None
    assert stored_result.status == "confirmed"
    assert stored_result.confirmed_by == opponent_id
