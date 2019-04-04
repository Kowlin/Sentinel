from .antirp import AntiRP


async def setup(bot):
    bot.add_cog(AntiRP(bot))
