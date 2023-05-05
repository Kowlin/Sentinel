from redbot.core.errors import CogLoadError


async def setup(bot):
    raise CogLoadError(
        "Hi there! This cog is no longer needed when using Red 3.5.0 or higher."
        " You can just uninstall it and use official support for slash commands instead!"
    )
