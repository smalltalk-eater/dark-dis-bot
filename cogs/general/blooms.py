import discord

from discord import app_commands
from discord.ext import commands

from config.blooms import BLOOMS
from services.blooms import get_bloom_collection
from utils.embeds import eden_embed


class Blooms(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot

    @app_commands.command(
        name="цветы",
        description="Посмотреть коллекцию редких Blooms участника",
    )
    @app_commands.guild_only()
    async def blooms(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
    ) -> None:
        if interaction.guild is None:
            return

        if user is None:
            if not isinstance(interaction.user, discord.Member):
                return
            user = interaction.user

        await interaction.response.defer()

        collection = await get_bloom_collection(
            guild_id=interaction.guild.id,
            user_id=user.id,
        )

        lines = []
        discovered = 0
        total = 0

        for key, bloom in BLOOMS.items():
            amount = collection.get(key, 0)
            total += amount

            if amount > 0:
                discovered += 1
                marker = "◆"
            else:
                marker = "◇"

            lines.append(
                (
                    f"{marker} **{bloom.name}** · `{bloom.rarity}` · "
                    f"**{amount}**\n"
                    f"{bloom.description}"
                )
            )

        embed = eden_embed(
            title=f"✦ BLOOMS · {user.display_name}",
            description="\n\n".join(lines),
        )

        embed.set_thumbnail(
            url=user.display_avatar.url
        )

        embed.set_footer(
            text=(
                "LOST EDEN · RIMAY  •  "
                f"{discovered}/{len(BLOOMS)} видов · {total} всего"
            )
        )

        await interaction.followup.send(
            embed=embed
        )


async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        Blooms(bot)
    )
