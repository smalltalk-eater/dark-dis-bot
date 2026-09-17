import discord

from discord import app_commands
from discord.ext import commands

from config.blooms import BLOOMS
from services.blooms import add_bloom
from utils.embeds import success_embed


BLOOM_CHOICES = [
    app_commands.Choice(
        name=f"{bloom.name} · {bloom.rarity}",
        value=bloom.key,
    )
    for bloom in BLOOMS.values()
]


class BloomsAdmin(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot

    @app_commands.command(
        name="выдать-bloom",
        description="Выдать редкий Bloom участнику",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    @app_commands.choices(
        bloom=BLOOM_CHOICES
    )
    async def grant_bloom_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        bloom: app_commands.Choice[str],
        amount: app_commands.Range[int, 1, 20] = 1,
    ) -> None:
        if interaction.guild is None:
            return

        definition = BLOOMS[bloom.value]

        total = await add_bloom(
            guild_id=interaction.guild.id,
            user_id=user.id,
            bloom_key=bloom.value,
            amount=amount,
        )

        await interaction.response.send_message(
            embed=success_embed(
                title="Bloom передан",
                description=(
                    f"{user.mention} получает **{definition.name}** "
                    f"× **{amount}**.\n\n"
                    f"Теперь в коллекции: **{total}**."
                ),
            ),
            ephemeral=True,
        )


async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        BloomsAdmin(bot)
    )
