from .freshmeat import Freshmeat


async def setup(bot):
    freshmeat = Freshmeat(bot)
    bot.add_cog(freshmeat)
