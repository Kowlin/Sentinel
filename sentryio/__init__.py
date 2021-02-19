from .core import SentryIO

__red_end_user_data_statement__ = "This cog steals your data and uploads it to Sentry.IO GLHF **I swear if I don't change this**"


async def setup(bot):
    cog = SentryIO(bot)
    await cog.initialize()
    try:
        bot.add_cog(cog)
    except Exception:
        # if adding cog causes an error, we want Sentry client to close itself
        cog.cog_unload()
