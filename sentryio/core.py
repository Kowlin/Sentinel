import asyncio
import logging
from typing import Mapping, Optional

import discord
import sentry_sdk
from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import inline
from redbot.core.utils.views import SetApiView
from sentry_sdk import add_breadcrumb
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

log = logging.getLogger("red.sentinel.sentryio.core")


class SentryIO(commands.Cog):
    """Sentry.IO Logger integration"""

    def __init__(self, bot: Red):
        self.bot = bot

    async def cog_load(self) -> None:
        asyncio.create_task(self.startup())

    def cog_unload(self) -> None:
        self.close_sentry()

    async def red_get_data_for_user(self, **kwargs):
        return {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    async def _get_dsn(self, api_tokens: Optional[Mapping[str, str]] = None) -> str:
        """Get Sentry DSN."""
        if api_tokens is None:
            api_tokens = await self.bot.get_shared_api_tokens("sentry")

        dsn = api_tokens.get("dsn", "")  # type: ignore
        if not dsn:
            log.error("No valid DSN found")
        return dsn

    def init_sentry(self, dsn: str) -> None:
        self.close_sentry()
        if not dsn:
            return
        log.info("Initializing Sentry with DSN: %s", dsn)
        sentry_sdk.init(
            dsn,
            traces_sample_rate=1.0,
            shutdown_timeout=0,
            integrations=[
                AioHttpIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
        )

    def close_sentry(self) -> None:
        client = sentry_sdk.Hub.current.client
        if client is not None:
            log.info("Closing Sentry client")
            client.close(timeout=0)

    async def startup(self) -> None:
        self.init_sentry(await self._get_dsn())

    @commands.group(name="sentryio")  # type: ignore
    @checks.is_owner()
    async def sentry_group(self, ctx):
        """Configure Sentry.IO stuffies"""  # TODO

    @sentry_group.command(name="status")
    async def status(self, ctx):
        """Check the status of Sentry.IO integration."""
        client = sentry_sdk.Hub.current.client
        if client is None:
            await ctx.send("Sentry.IO is not initialized.")
            return
        await ctx.send(
            f"Sentry.IO is initialized with DSN: {inline(client.options['dsn'])}"
        )

    @sentry_group.command(name="instructions")
    async def instructions(self, ctx):
        """
        Learn on how to setup SentryIO cog.

        *This will be the SECOND time that someone will ACTUALLY read instructions*
        """
        message = (
            "1. Go to Settings page of your Sentry Account at <https://sentry.io/settings>\n"
            "2. Go to Projects list and select the project you want to use for this bot.\n"
            "3. Select Client Keys (DSN) menu entry at the left.\n"
            "4. Copy your DSN and click the button below to set your DSN."
        )
        api_tokens = await self.bot.get_shared_api_tokens("sentry")
        await ctx.send(
            message,
            view=SetApiView(
                default_service="sentry",
                default_keys={"dsn": api_tokens.get("dsn", "")},
            ),
        )

    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ):
        if service_name != "sentry":
            return
        self.init_sentry(await self._get_dsn(api_tokens))

    def prepare_crumbs_commands(self, ctx: commands.Context) -> Mapping[str, str]:
        crumb_data = {
            "command_name": getattr(ctx.command, "qualified_name", "None"),
            "cog_name": getattr(ctx.command.cog, "qualified_name", "None"),
            "author_id": getattr(ctx.author, "id", "None"),
            "guild_id": getattr(ctx.guild, "id", "None"),
            "channel_id": getattr(ctx.channel, "id", "None"),
        }
        for comm_arg, value in ctx.kwargs.items():
            crumb_data[f"command_arg_{comm_arg}"] = value
        return crumb_data
    
    def prepare_crumbs_interactions(self, interaction: discord.Interaction) -> Mapping[str, str]:
        crumb_data = {
            "interaction_id": getattr(interaction, "id", "None"),
            "channel_id": getattr(interaction.channel, "id", "None"),
            "guild_id": getattr(interaction.guild, "id", "None"),
            "user_id": getattr(interaction.user, "id", "None"),
            "message_id": getattr(interaction.message, "id", "None"),
        }
        return crumb_data

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if not ctx.command:
            return

        crumb_data = self.prepare_crumbs_commands(ctx)
        add_breadcrumb(
            type="user",
            category="on_command_error",
            message=f'Command "{ctx.command.qualified_name}" failed for {ctx.author.name} ({ctx.author.id})',
            level="error",
            data=crumb_data,
        )

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        crumb_data = self.prepare_crumbs_commands(ctx)
        add_breadcrumb(
            type="user",
            category="on_command",
            message=f'Command "{ctx.command.qualified_name}" ran for {ctx.author.name} ({ctx.author.id})',
            level="info",
            data=crumb_data,
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        crumb_data = self.prepare_crumbs_commands(ctx)
        add_breadcrumb(
            type="user",
            category="on_command_completion",
            message=f'Command "{ctx.command.qualified_name}" completed for {ctx.author.name} ({ctx.author.id})',
            level="info",
            data=crumb_data,
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        crumb_data = self.prepare_crumbs_interactions(interaction)
        add_breadcrumb(
            type="user",
            category="on_interaction",
            message=f'Interaction "{interaction.id}" ran for {interaction.user.name} ({interaction.user.id})',
            level="info",
            data=crumb_data,
        )
