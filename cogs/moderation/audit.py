import json

import discord

from discord import app_commands
from discord.ext import commands

from database.audit import (
    get_recent_audit,
    record_audit,
)
from utils.embeds import eden_embed


AUDITED_COMMANDS = {
    "панель-верификации",
    "верифицировать",
    "снять-верификацию",
    "добавить-опыт",
    "добавить-средства",
    "снять-средства",
    "обновить-роль-уровня",
    "повторить-награды",
    "роль-уровня",
    "выдать-цветок",
    "тест-баннера",
    "создать-ивент",
    "запустить-ивент",
    "завершить-ивент",
    "отменить-ивент",
    "награда-ивента",
    "отменить-дуэль",
    "создать-клоз",
    "запустить-клоз",
    "результат-клоза",
    "подтвердить-клоз",
    "отменить-клоз",
}


def serialize_value(value) -> str | int | float | bool | None:
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, app_commands.Choice):
        return str(value.value)

    if isinstance(value, (discord.User, discord.Member, discord.Role)):
        return value.id

    return str(value)[:200]


def interaction_details(
    interaction: discord.Interaction,
) -> dict:
    namespace = getattr(
        interaction,
        "namespace",
        None,
    )

    if namespace is None:
        return {}

    raw_values = getattr(
        namespace,
        "__dict__",
        {},
    )

    return {
        key: serialize_value(value)
        for key, value in raw_values.items()
        if not key.startswith("_")
    }


def format_details(raw: str | None) -> str:
    if not raw:
        return ""

    try:
        values = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:180]

    if not isinstance(values, dict):
        return str(values)[:180]

    parts = [
        f"{key}={value}"
        for key, value in values.items()
    ]

    return ", ".join(parts)[:180]


class Audit(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command,
    ) -> None:
        if interaction.guild is None:
            return

        command_name = getattr(
            command,
            "qualified_name",
            "",
        )

        if command_name not in AUDITED_COMMANDS:
            return

        try:
            await record_audit(
                guild_id=interaction.guild.id,
                actor_id=interaction.user.id,
                action=command_name,
                details=interaction_details(interaction),
            )
        except Exception as error:
            print(f"[AUDIT] {error}")

    @app_commands.command(
        name="аудит",
        description="Показать последние административные действия",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def audit_log(
        self,
        interaction: discord.Interaction,
        количество: app_commands.Range[int, 1, 25] = 10,
    ) -> None:
        if interaction.guild is None:
            return

        entries = await get_recent_audit(
            guild_id=interaction.guild.id,
            limit=количество,
        )

        if not entries:
            description = "Журнал пока пуст."
        else:
            lines = []

            for entry in entries:
                details = format_details(entry.details)
                suffix = f" · `{details}`" if details else ""

                lines.append(
                    (
                        f"**/{entry.action}** · <@{entry.actor_id}>"
                        f"{suffix}\n"
                        f"<t:{entry.created_at}:R>"
                    )
                )

            description = "\n\n".join(lines)

        await interaction.response.send_message(
            embed=eden_embed(
                title="✦ ADMIN AUDIT",
                description=description,
            ),
            ephemeral=True,
        )


async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        Audit(bot)
    )
