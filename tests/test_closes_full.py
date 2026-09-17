import pytest

from database.member_stats import get_member_stats
from services.activities import create_activity, join_activity
from services.close_results import (
    confirm_close_result,
    get_close_result,
    propose_close_result,
)
from services.close_rewards import reward_close_automatically
from services.close_teams import (
    TEAM_MODE_CAPTAINS,
    create_close_settings,
    get_close_settings,
    get_close_teams,
    pick_close_player,
)
from services.closes import start_close


async def create_captain_close(guild_id: int):
    activity = await create_activity(
        guild_id=guild_id,
        activity_type="close",
        title="Captain CLOSE",
        description="",
        host_id=999,
        max_participants=4,
    )

    await create_close_settings(
        activity_id=activity.activity_id,
        team_mode=TEAM_MODE_CAPTAINS,
    )

    for user_id in (201, 202, 203, 204):
        assert await join_activity(
            guild_id=guild_id,
            activity_id=activity.activity_id,
            user_id=user_id,
        ) == "joined"

    return activity


@pytest.mark.asyncio
async def test_captain_close_draft_confirmation_and_rewards(test_db):
    guild_id = 740
    activity = await create_captain_close(guild_id)

    started = await start_close(
        guild_id=guild_id,
        activity_id=activity.activity_id,
    )

    assert started.status == "started"
    assert started.captain_a_id is not None
    assert started.captain_b_id is not None

    settings = await get_close_settings(activity.activity_id)
    teams = await get_close_teams(activity.activity_id)

    assert settings is not None
    assert settings.draft_turn in {"a", "b"}
    assert len(teams.waiting) == 2

    wrong_captain = (
        settings.captain_b_id
        if settings.draft_turn == "a"
        else settings.captain_a_id
    )

    assert wrong_captain is not None

    wrong_turn = await pick_close_player(
        activity_id=activity.activity_id,
        captain_id=wrong_captain,
        player_id=teams.waiting[0],
    )
    assert wrong_turn == "wrong_turn"

    first_captain = (
        settings.captain_a_id
        if settings.draft_turn == "a"
        else settings.captain_b_id
    )
    first_player = teams.waiting[0]

    assert first_captain is not None

    first_pick = await pick_close_player(
        activity_id=activity.activity_id,
        captain_id=first_captain,
        player_id=first_player,
    )
    assert first_pick == "picked"

    duplicate = await pick_close_player(
        activity_id=activity.activity_id,
        captain_id=first_captain,
        player_id=first_player,
    )
    assert duplicate in {"wrong_turn", "already_picked"}

    settings = await get_close_settings(activity.activity_id)
    teams = await get_close_teams(activity.activity_id)

    assert settings is not None
    assert len(teams.waiting) == 1

    second_captain = (
        settings.captain_a_id
        if settings.draft_turn == "a"
        else settings.captain_b_id
    )
    assert second_captain is not None

    final_pick = await pick_close_player(
        activity_id=activity.activity_id,
        captain_id=second_captain,
        player_id=teams.waiting[0],
    )
    assert final_pick == "finished"

    teams = await get_close_teams(activity.activity_id)
    assert len(teams.team_a) == 2
    assert len(teams.team_b) == 2
    assert teams.waiting == []

    proposed = await propose_close_result(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        winner_team="a",
        submitted_by=999,
    )
    assert proposed == "created"

    settings = await get_close_settings(activity.activity_id)
    assert settings is not None
    assert settings.captain_b_id is not None

    status, finished = await confirm_close_result(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        confirmed_by=settings.captain_b_id,
    )

    assert status == "confirmed"
    assert finished is not None
    assert finished.status == "finished"

    rewards = await reward_close_automatically(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        actor_id=999,
    )

    assert rewards

    for user_id in teams.team_a:
        stats = await get_member_stats(
            guild_id=guild_id,
            user_id=user_id,
        )
        assert stats.xp == 15
        assert stats.currency == 10

    for user_id in teams.team_b:
        stats = await get_member_stats(
            guild_id=guild_id,
            user_id=user_id,
        )
        assert stats.xp == 5
        assert stats.currency == 0

    second_rewards = await reward_close_automatically(
        guild_id=guild_id,
        activity_id=activity.activity_id,
        actor_id=999,
    )

    assert second_rewards
    assert all(
        item.status == "already_granted"
        for item in second_rewards
    )

    stored = await get_close_result(activity.activity_id)
    assert stored is not None
    assert stored.status == "confirmed"
