import discord

from discord import app_commands
from discord.ext import commands

from config.economy import (
    CURRENCY_SYMBOL,
    SHOP_CASE_PRICE,
    SHOP_MAX_CASES_PER_PURCHASE,
)
from database.economy import get_balance
from services.shop import buy_eden_cases
from utils.embeds import (
    eden_embed,
    error_embed,
    success_embed,
)


class Shop(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot

    @app_commands.command(
        name="магазин",
        description="Открыть магазин LOST EDEN",
    )
    @app_commands.guild_only()
    async def shop(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            return

        balance = await get_balance(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
        )

        embed = eden_embed(
            title="✦ МАГАЗИН LOST EDEN",
            description=(
                "Здесь средства можно обменять на редкие вещи Сада.\n\n"
                "Сейчас доступен **EDEN CASE**. Он может принести "
                "средства, XP и редкий Bloom."
            ),
        )

        embed.add_field(
            name="EDEN CASE",
            value=(
                f"Цена: **{SHOP_CASE_PRICE} {CURRENCY_SYMBOL}**\n"
                "Покупка: `/купить-кейс`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Твой баланс",
            value=f"**{balance} {CURRENCY_SYMBOL}**",
            inline=False,
        )

        embed.set_footer(
            text=(
                "Основной источник EDEN CASES — уровни, достижения и события"
            )
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @app_commands.command(
        name="купить-кейс",
        description="Купить EDEN CASE за средства",
    )
    @app_commands.guild_only()
    async def buy_case(
        self,
        interaction: discord.Interaction,
        количество: app_commands.Range[
            int,
            1,
            SHOP_MAX_CASES_PER_PURCHASE,
        ] = 1,
    ) -> None:
        if interaction.guild is None:
            return

        result = await buy_eden_cases(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            amount=количество,
        )

        if result.status == "insufficient_funds":
            await interaction.response.send_message(
                embed=error_embed(
                    title="Недостаточно средств",
                    description=(
                        f"Нужно **{result.total_cost} {CURRENCY_SYMBOL}**, "
                        f"а на балансе **{result.new_balance} {CURRENCY_SYMBOL}**."
                    ),
                ),
                ephemeral=True,
            )
            return

        if result.status != "purchased":
            await interaction.response.send_message(
                embed=error_embed(
                    title="Покупка не выполнена",
                    description="Проверь количество и попробуй ещё раз.",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=success_embed(
                title="Покупка завершена",
                description=(
                    f"Получено EDEN CASE: **{result.amount}**\n"
                    f"Списано: **{result.total_cost} {CURRENCY_SYMBOL}**\n"
                    f"Баланс: **{result.new_balance} {CURRENCY_SYMBOL}**\n"
                    f"Кейсов в хранилище: **{result.new_cases}**"
                ),
            ),
            ephemeral=True,
        )


async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        Shop(bot)
    )
