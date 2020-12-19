from .core import SlashInjector


async def setup(bot):
    cog = SlashInjector(bot)
    bot.add_cog(cog)
