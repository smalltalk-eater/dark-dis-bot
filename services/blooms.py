import secrets

from config.blooms import (
    BLOOMS,
    BLOOM_CASE_DROP_CHANCE,
    BloomDefinition,
)
from database.blooms import (
    get_member_blooms,
    grant_bloom,
)


randomizer = secrets.SystemRandom()


def get_bloom(
    bloom_key: str,
) -> BloomDefinition | None:
    return BLOOMS.get(bloom_key)


def roll_case_bloom() -> BloomDefinition | None:
    if randomizer.random() >= BLOOM_CASE_DROP_CHANCE:
        return None

    blooms = list(BLOOMS.values())

    return randomizer.choices(
        blooms,
        weights=[bloom.weight for bloom in blooms],
        k=1,
    )[0]


async def add_bloom(
    guild_id: int,
    user_id: int,
    bloom_key: str,
    amount: int = 1,
) -> int:
    if bloom_key not in BLOOMS:
        raise ValueError("Неизвестный Bloom")

    return await grant_bloom(
        guild_id=guild_id,
        user_id=user_id,
        bloom_key=bloom_key,
        amount=amount,
    )


async def get_bloom_collection(
    guild_id: int,
    user_id: int,
) -> dict[str, int]:
    stored = await get_member_blooms(
        guild_id=guild_id,
        user_id=user_id,
    )

    return {
        key: stored.get(key, 0)
        for key in BLOOMS
    }
