from .butts import Butts

__red_end_user_data_statement__ = "Butts stores no user data."


async def setup(bot):
    c = Butts(bot)
    bot.add_cog(c)
