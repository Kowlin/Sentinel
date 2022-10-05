from .antirp import AntiRP

__red_end_user_data_statement__ = "AntiRP stores no personal information."


async def setup(bot):
    await bot.add_cog(AntiRP(bot))
