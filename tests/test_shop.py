import pytest

from config.economy import SHOP_CASE_PRICE
from database.economy import change_balance, get_balance
from database.member_stats import get_member_stats
from services.shop import buy_eden_cases


@pytest.mark.asyncio
async def test_shop_buys_cases_atomically(test_db):
    guild_id = 700
    user_id = 71

    await change_balance(
        guild_id=guild_id,
        user_id=user_id,
        amount=300,
        reason="test",
    )

    result = await buy_eden_cases(
        guild_id=guild_id,
        user_id=user_id,
        amount=2,
    )

    stats = await get_member_stats(
        guild_id=guild_id,
        user_id=user_id,
    )

    assert result.status == "purchased"
    assert result.total_cost == SHOP_CASE_PRICE * 2
    assert stats.eden_cases == 2
    assert stats.currency == 300 - SHOP_CASE_PRICE * 2
    assert await get_balance(guild_id, user_id) == stats.currency


@pytest.mark.asyncio
async def test_shop_rejects_purchase_without_funds(test_db):
    guild_id = 701
    user_id = 72

    result = await buy_eden_cases(
        guild_id=guild_id,
        user_id=user_id,
        amount=1,
    )

    stats = await get_member_stats(
        guild_id=guild_id,
        user_id=user_id,
    )

    assert result.status == "insufficient_funds"
    assert stats.currency == 0
    assert stats.eden_cases == 0
