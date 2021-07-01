import asyncio

from redbot.core.bot import Red

from .core import GitHubCards

__red_end_user_data_statement__ = "GitHubCards stores no personal information."


async def setup(bot: Red) -> None:
    cog = GitHubCards(bot)
    bot.add_cog(cog)
    asyncio.create_task(cog.initialize())
