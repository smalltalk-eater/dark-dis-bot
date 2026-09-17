import discord
import pytest

from discord.ext import commands

from cogs.general import general
from cogs.general import profile


@pytest.mark.asyncio
async def test_profile_command_has_single_implementation():
    bot = commands.Bot(
        command_prefix="!",
        intents=discord.Intents.none(),
    )

    await general.setup(bot)

    # General больше не должен регистрировать старую реализацию /профиль.
    assert bot.tree.get_command("профиль") is None

    await profile.setup(bot)

    current_command = bot.tree.get_command("профиль")

    assert current_command is not None
    assert bot.get_cog("Profile") is not None
