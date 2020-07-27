from .freshmeat import Freshmeat

__red_end_user_data_statement__ = "Freshmeat stores no user data."


async def setup(bot):
    freshmeat = Freshmeat(bot)
    bot.add_cog(freshmeat)
