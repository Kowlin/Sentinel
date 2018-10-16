from .massmove import Massmove


def setup(bot):
    bot.add_cog(Massmove(bot))
