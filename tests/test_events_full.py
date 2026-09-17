import pytest

from database.member_stats import get_member_stats
from services.activities import (
    change_activity_status,
    create_activity,
    join_activity,
)
from services.automatic_activity_rewards import reward_event_automatically


@pytest.mark.asyncio
async def test_event_full_reward_flow_is_idempotent(test_db):
    guild_id = 750
    users = (301, 302)

    activity = await create_activity(
        guild_id=guild_id,
        activity_type="event",
        title="Full EVENT",
        description="",
        host_id=999,
        max_participants=10,
        reward_preset="custom:20:30:1",
    )

    for user_id in users:
        assert await join_activity(
            guild_id=guild_id,
            activity_id=activity.activity_id,
            user_id=user_id,
        ) == "joined"

    status, _ = await change_activity_status(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        new_status="running",
    )
    assert status == "changed"

    status, finished = await change_activity_status(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        new_status="finished",
    )
    assert status == "changed"
    assert finished is not None

    first = await reward_event_automatically(
        activity=finished,
        actor_id=999,
    )

    assert len(first) == 6
    assert all(item.status == "granted" for item in first)

    for user_id in users:
        stats = await get_member_stats(
            guild_id=guild_id,
            user_id=user_id,
        )

        assert stats.currency == 20
        assert stats.xp == 30
        assert stats.eden_cases == 1

    second = await reward_event_automatically(
        activity=finished,
        actor_id=999,
    )

    assert len(second) == 6
    assert all(item.status == "already_granted" for item in second)

    for user_id in users:
        stats = await get_member_stats(
            guild_id=guild_id,
            user_id=user_id,
        )

        assert stats.currency == 20
        assert stats.xp == 30
        assert stats.eden_cases == 1
