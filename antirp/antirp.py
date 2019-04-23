import discord
from redbot.core import commands, checks, Config

BaseCog = getattr(commands, "Cog", object)


class AntiRP(BaseCog):
    """AntiRP: For when hiding buttons in the Discord UI isn't enough."""

    def_guild = {
        "toggle": False,
        "whitelist": []
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25360008)

        self.config.register_guild(**self.def_guild)

    @checks.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def antirp(self, ctx):
        """Manage the settings for AntiRP"""
        pass

    @antirp.command()
    async def toggle(self, ctx, true_or_false: bool = None):
        """Toggle AntiRP on or off"""
        if true_or_false is None:
            toggle_config = await self.config.guild(ctx.guild).toggle()
            if toggle_config is True:
                await self.config.guild(ctx.guild).toggle.set(False)
                await ctx.send(f"Done! Turned off AntiRP")
            else:
                await self.config.guild(ctx.guild).toggle.set(True)
                await ctx.send(f"Done! Turned on AntiRP")
        else:
            await self.config.guild(ctx.guild).toggle.set(true_or_false)
            await ctx.tick()

    @antirp.command()
    async def grabname(self, ctx, channel: discord.TextChannel, messageID: int):
        """Grab an application name via RP Invite"""
        try:
            message = await channel.get_message(messageID)
        except discord.NotFound:
            return await ctx.send("Couldn't find the message you're looking for.")

        # Since invites all use party IDs we can savely assume that this is a RP invite.
        if message.activity is None:
            return await ctx.send("This message has no rich presence invite")

        # Check if this is spotify or not... Since spotify is SPECIAL! T_T
        if message.activity["party_id"].startswith("spotify:"):
            return await ctx.send("Application name: Spotify")
        return await ctx.send(f"Application name: {message.application['name']}")

    @antirp.group()
    async def whitelist(self, ctx):
        """Manage the application whitelist for AntiRP

        When an application is added to the whitelist,
        any other applications not matching the name will be removed.
        Regardless if the permissions are valid.

        Even though Spotify isn't an application it can be added as a whitelisted application"""
        pass

    @whitelist.command(name="add", usage="<Application name>")
    async def wl_add(self, ctx, *, application_name: str):
        """Add a new whitelisted application"""
        whitelist_config = await self.config.guild(ctx.guild).whitelist()
        whitelist_config.append(application_name.lower())
        await self.config.guild(ctx.guild).whitelist.set(whitelist_config)
        await ctx.tick()

    @whitelist.command(name="remove", usage="<Application name>")
    async def wl_remove(self, ctx, *, application_name: str):
        """Remove a whitelisted application"""
        whitelist_config = await self.config.guild(ctx.guild).whitelist()
        whitelist_config.remove(application_name.lower())
        await self.config.guild(ctx.guild).whitelist.set(whitelist_config)
        await ctx.tick()

    @whitelist.command(name="clear")
    async def wl_clear(self, ctx):
        """Remove all whitelisted applications"""
        await self.config.guild(ctx.guild).whitelist.set([])
        await ctx.tick()

    @whitelist.command(name="list")
    async def wl_list(self, ctx):
        """List all the whitelisted applications"""
        whitelist_config = await self.config.guild(ctx.guild).whitelist()
        humanized_whitelist = ", ".join(whitelist_config)
        if len(whitelist_config) != 0:
            await ctx.send(f"Whitelisted applications:\n{humanized_whitelist}")
        else:
            await ctx.send("No applications are whitelisted.")

    async def on_message(self, message):
        if message.guild is None:
            return

        guild_config = self.config.guild(message.guild)
        toggle_config = await guild_config.toggle()
        whitelist_config = await guild_config.whitelist()

        if message.activity is None or toggle_config is False:
            return
        if await self.bot.is_automod_immune(message.author) is True:
            return  # End it because we're dealing with a mod.

        if message.channel.permissions_for(message.author).embed_links is False:
            try:
                return await message.delete()
            except discord.Forbidden:
                return

        if len(whitelist_config) != 0:
            # We got entries in the whitelist, do special checks.
            if "spotify" in whitelist_config and message.activity["party_id"].startswith("spotify:"):
                return  # Deal with spotify in the whitelist
            if message.application is not None and message.application["name"].lower() in whitelist_config:
                return  # Deal with applications in the whitelist
            try:
                return await message.delete()  # Handle not in whitelists.
            except:
                return
