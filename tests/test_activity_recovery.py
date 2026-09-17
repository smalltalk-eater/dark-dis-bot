import pytest

from services.activities import (
    change_activity_status,
    create_activity,
    get_open_activities,
    set_activity_message,
)
from services.duels import (
    create_duel,
    get_pending_duel_results,
    propose_duel_result,
)


@pytest.mark.asyncio
async def test_open_event_is_recoverable_after_restart(test_db):
    guild_id = 760

    activity = await create_activity(
        guild_id=guild_id,
        activity_type="event",
        title="Recover EVENT",
        description="",
        host_id=999,
        max_participants=10,
    )

    await set_activity_message(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        channel_id=123,
        message_id=456,
    )

    recovered = await get_open_activities(
        guild_id=guild_id,
        activity_type="event",
    )

    assert len(recovered) == 1
    assert recovered[0].activity_id == activity.activity_id
    assert recovered[0].channel_id == 123
    assert recovered[0].message_id == 456


@pytest.mark.asyncio
async def test_pending_duel_result_is_recoverable_after_restart(test_db):
    guild_id = 761

    created = await create_duel(
        guild_id=guild_id,
        challenger_id=401,
        opponent_id=402,
        title="Recover DUEL",
    )

    assert created.activity is not None
    activity_id = created.activity.activity_id

    await set_activity_message(
        guild_id=guild_id,
        activity_id=activity_id,
        channel_id=124,
        message_id=457,
    )

    status, _ = await change_activity_status(
        guild_id=guild_id,
        activity_id=activity_id,
        new_status="running",
    )
    assert status == "changed"

    result_status, _ = await propose_duel_result(
        guild_id=guild_id,
        activity_id=activity_id,
        winner_id=401,
        submitted_by=401,
    )
    assert result_status == "created"

    recovered = await get_pending_duel_results(
        guild_id=guild_id,
    )

    assert len(recovered) == 1
    assert recovered[0].activity_id == activity_id
    assert recovered[0].winner_id == 401
    assert recovered[0].status == "pending"
