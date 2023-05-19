import logging
from typing import Mapping, Optional

import discord
import sentry_sdk
from redbot.core import checks, commands
from redbot.core.utils.chat_formatting import inline
from redbot.core.utils.views import SetApiView
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk import add_breadcrumb

log = logging.getLogger("red.sentinel.sentryio.core")


class SentryIO(commands.Cog):
    """Sentry.IO Logger integration"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.init_sentry(await self._get_dsn())

    def cog_unload(self) -> None:
        client = sentry_sdk.Hub.current.client
        if client is not None:
            client.close()

    async def red_get_data_for_user(self, **kwargs):
        return {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    async def _get_dsn(self, api_tokens: Optional[Mapping[str, str]] = None) -> str:
        """Get Sentry DSN."""
        if api_tokens is None:
            api_tokens = await self.bot.get_shared_api_tokens("sentry")

        dsn = api_tokens.get("dsn", "")
        if not dsn:
            log.error("No valid DSN found")
        return dsn

    def init_sentry(self, dsn: str) -> None:
        self.close_sentry()
        sentry_sdk.init(
            dsn,
            traces_sample_rate=1.0,
            shutdown_timeout=0.1,
            integrations=[
                AioHttpIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ]
        )

    def close_sentry(self) -> None:
        client = sentry_sdk.Hub.current.client
        if client is not None:
            client.close()

    @commands.group(name="sentryio")
    @checks.is_owner()
    async def sentry_group(self, ctx):
        """Configure Sentry.IO stuffies"""  # TODO

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
        await ctx.send(
            message,
            view=SetApiView(default_service="sentry", default_keys={"dsn": ""}),
        )

    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ):
        if service_name != "sentry":
            return
        self.init_sentry(await self._get_dsn(api_tokens))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not ctx.command:
            return
        add_breadcrumb(
            type="user",
            category="on_command_error",
            message=f"command \"{ctx.command.qualified_name}\" failed for {ctx.author.name} ({ctx.author.id})",
            level="error"
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        add_breadcrumb(
            type="user",
            category="on_command",
            message=f"command \"{ctx.command.qualified_name}\" ran for {ctx.author.name} ({ctx.author.id})",
            level="info"
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        add_breadcrumb(
            type="user",
            category="on_command_completion",
            message=f"command \"{ctx.command.qualified_name}\" completed for {ctx.author.name} ({ctx.author.id})",
            level="info"
        )
