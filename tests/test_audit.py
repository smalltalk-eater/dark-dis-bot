import pytest

from database.audit import get_recent_audit, record_audit


@pytest.mark.asyncio
async def test_admin_audit_keeps_recent_actions(test_db):
    guild_id = 720

    await record_audit(
        guild_id=guild_id,
        actor_id=1,
        action="верифицировать",
        details={"user": 10},
    )
    await record_audit(
        guild_id=guild_id,
        actor_id=2,
        action="добавить-средства",
        details={"user": 10, "amount": 25},
    )

    entries = await get_recent_audit(
        guild_id=guild_id,
        limit=10,
    )

    assert len(entries) == 2
    assert entries[0].action == "добавить-средства"
    assert entries[0].actor_id == 2
    assert '"amount":25' in (entries[0].details or "")
    assert entries[1].action == "верифицировать"
