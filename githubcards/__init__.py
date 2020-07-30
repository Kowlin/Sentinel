from redbot import version_info, VersionInfo
from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from .core import GitHubCards

if version_info < VersionInfo.from_str("3.2.0"):
    raise CogLoadError("This cog requires at least Red 3.2.0 to work.")

__red_end_user_data_statement__ = "GitHubCards stores no personal information."


async def setup(bot: Red) -> None:
    cog = GitHubCards(bot)
    await cog.initialize()
    bot.add_cog(cog)
