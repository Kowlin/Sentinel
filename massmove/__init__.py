from .massmove import Massmove

__red_end_user_data_statement__ = "Massmove stores no personal information."


async def setup(bot):
    await bot.add_cog(Massmove(bot))
