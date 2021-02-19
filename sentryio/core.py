import logging
from typing import Mapping

import discord
import sentry_sdk
from redbot.core import checks, commands
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk import add_breadcrumb


class SentryIO(commands.Cog):
    """Sentry.IO Logger integration"""

    def __init__(self, bot):
        self.bot = bot
        sentry_sdk.init(
            "DAMNURLHERE",
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

    def _cog_unload(self):
        client = sentry_sdk.Hub.current.client
        if client is not None:
            client.close()

    async def red_get_data_for_user(self, **kwargs):
        return {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    @checks.is_owner()
    @commands.command()
    async def plzerror(self, ctx):
        raise Exception

    @commands.group(name="sentryio")
    @checks.is_owner()
    async def sentry_group(self, ctx):
        """Configure Sentry.IO stuffies"""  # TODO

    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ):
        pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        add_breadcrumb(
            type="user",
            category="on_command_error",
            message=f"command \"{ctx.command.name}\" failed for {ctx.author.name} ({ctx.author.id})",
            level="error"
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        add_breadcrumb(
            type="user",
            category="on_command",
            message=f"command \"{ctx.command.name}\" ran for {ctx.author.name} ({ctx.author.id})",
            level="info"
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        add_breadcrumb(
            type="user",
            category="on_command_completion",
            message=f"command \"{ctx.command.name}\" completed for {ctx.author.name} ({ctx.author.id})",
            level="info"
        )
