from redbot.core.bot import Red

from .core import GitHubCards

__red_end_user_data_statement__ = "GitHubCards stores no personal information."


async def setup(bot: Red) -> None:
    cog = GitHubCards(bot)
    await cog.initialize()
    bot.add_cog(cog)
