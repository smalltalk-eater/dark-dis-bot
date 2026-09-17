import discord

from discord import app_commands
from discord.ext import commands

from config.roles import LEVEL_ROLES
from database.connection import get_db
from services.verification_roles import get_verified_role_id
from utils.embeds import eden_embed
from utils.profile_card_v2 import PROFILE_TEMPLATE_V2


def check_line(
    ok: bool,
    title: str,
    detail: str,
) -> str:
    marker = "OK" if ok else "ERROR"
    return f"**[{marker}] {title}**\n{detail}"


class SystemCheck(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot

    @app_commands.command(
        name="проверка-системы",
        description="Проверить роли, права, базу и шаблон профиля",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def system_check(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            return

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild
        lines = []

        db_ok = True
        db_detail = "SQLite отвечает."

        try:
            async with get_db() as db:
                cursor = await db.execute("SELECT 1")
                await cursor.fetchone()
                await cursor.close()
        except Exception as error:
            db_ok = False
            db_detail = f"Ошибка базы: {error}"

        lines.append(
            check_line(
                db_ok,
                "База данных",
                db_detail,
            )
        )

        template_ok = PROFILE_TEMPLATE_V2.exists()
        lines.append(
            check_line(
                template_ok,
                "Шаблон профиля",
                (
                    str(PROFILE_TEMPLATE_V2)
                    if template_ok
                    else f"Не найден: {PROFILE_TEMPLATE_V2}"
                ),
            )
        )

        bot_member = guild.me

        if bot_member is None and self.bot.user is not None:
            bot_member = guild.get_member(self.bot.user.id)

        if bot_member is None:
            lines.append(
                check_line(
                    False,
                    "Роль бота",
                    "Discord не вернул Member-объект бота.",
                )
            )
        else:
            required_permissions = {
                "Управлять ролями": bot_member.guild_permissions.manage_roles,
                "Отправлять сообщения": bot_member.guild_permissions.send_messages,
                "Встраивать ссылки": bot_member.guild_permissions.embed_links,
                "Прикреплять файлы": bot_member.guild_permissions.attach_files,
            }

            missing_permissions = [
                name
                for name, enabled in required_permissions.items()
                if not enabled
            ]

            lines.append(
                check_line(
                    not missing_permissions,
                    "Права бота",
                    (
                        "Нужные права выданы."
                        if not missing_permissions
                        else (
                            "Не хватает: "
                            + ", ".join(missing_permissions)
                        )
                    ),
                )
            )

        try:
            verified_role_id = get_verified_role_id()
        except RuntimeError as error:
            verified_role_id = None
            verification_error = str(error)
        else:
            verification_error = None

        verified_role = (
            guild.get_role(verified_role_id)
            if verified_role_id is not None
            else None
        )

        if verification_error is not None:
            verification_detail = verification_error
            verification_ok = False
        elif verified_role_id is None:
            verification_detail = "VERIFIED_ROLE_ID не указан в .env."
            verification_ok = False
        elif verified_role is None:
            verification_detail = (
                f"Роль с ID {verified_role_id} не найдена на сервере."
            )
            verification_ok = False
        elif bot_member is None:
            verification_detail = "Нельзя проверить иерархию ролей бота."
            verification_ok = False
        elif bot_member.top_role <= verified_role:
            verification_detail = (
                f"Роль бота должна быть выше роли {verified_role.name}."
            )
            verification_ok = False
        else:
            verification_detail = (
                f"Роль {verified_role.name} настроена и доступна боту."
            )
            verification_ok = True

        lines.append(
            check_line(
                verification_ok,
                "Верификация",
                verification_detail,
            )
        )

        milestone_missing = []
        milestone_unmanageable = []

        for role_name in LEVEL_ROLES.values():
            role = discord.utils.get(
                guild.roles,
                name=role_name,
            )

            if role is None:
                milestone_missing.append(role_name)
                continue

            if (
                bot_member is not None
                and bot_member.top_role <= role
            ):
                milestone_unmanageable.append(role_name)

        milestones_ok = (
            bool(LEVEL_ROLES)
            and not milestone_missing
            and not milestone_unmanageable
        )

        milestone_parts = []

        if not LEVEL_ROLES:
            milestone_parts.append("Юбилейные роли не настроены в config/roles.py.")
        if milestone_missing:
            milestone_parts.append(
                "Создай роли: " + ", ".join(milestone_missing)
            )
        if milestone_unmanageable:
            milestone_parts.append(
                "Подними роль бота выше: "
                + ", ".join(milestone_unmanageable)
            )
        if milestones_ok:
            milestone_parts.append("Все юбилейные роли найдены и доступны боту.")

        lines.append(
            check_line(
                milestones_ok,
                "Юбилейные роли",
                "\n".join(milestone_parts),
            )
        )

        all_ok = all(
            [
                db_ok,
                template_ok,
                verification_ok,
                milestones_ok,
                bot_member is not None,
            ]
        )

        await interaction.followup.send(
            embed=eden_embed(
                title=(
                    "✦ SYSTEM CHECK · READY"
                    if all_ok
                    else "✦ SYSTEM CHECK · NEEDS ATTENTION"
                ),
                description="\n\n".join(lines),
            ),
            ephemeral=True,
        )


async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        SystemCheck(bot)
    )
