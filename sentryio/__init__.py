from .core import SentryIO

__red_end_user_data_statement__ = "This cog does not record end user data."


async def setup(bot):
    cog = SentryIO(bot)
    try:
        await bot.add_cog(cog)
    except Exception:
        # if adding cog causes an error, we want Sentry client to close itself
        cog.cog_unload()
        raise
