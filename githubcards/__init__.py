from .core import GitHubCards


async def setup(bot):
    cog = GitHubCards(bot)
    await cog._set_token()
    bot.add_cog(cog)
