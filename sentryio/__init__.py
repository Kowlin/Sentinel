from .core import SentryIO

__red_end_user_data_statement__ = "This cog steals your data and uploads it to Sentry.IO GLHF **I swear if I don't change this**"


def setup(bot):
    bot.add_cog(SentryIO(bot))
