import discord

from redbot.core import commands
from redbot.core import checks

BaseCog = getattr(commands, "Cog", object)


class Massmove(BaseCog):

    def __init__(self, bot):
        self.bot = bot

    async def red_get_data_for_user(self, **kwargs):
        return {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    @checks.mod_or_permissions(move_members=True)
    @commands.group(autohelp=False, invoke_without_command=True)
    async def massmove(self, ctx, channel_from: discord.VoiceChannel, channel_to: discord.VoiceChannel):
        """Massmove members from one channel to another.

        This works the best if you enable Developer mode and copy the ID's for the channels.

        `channel_from`: The channel members will get moved from
        `channel_to`: The channel members will get moved to
        """
        await self.move_all_members(ctx, channel_from, channel_to)

    @checks.mod_or_permissions(move_members=True)
    @massmove.command()
    async def afk(self, ctx, channel_from: discord.VoiceChannel):
        """Massmove members to the AFK channel

        This works the best if you enable Developer mode and copy the ID for the channel

        `channel_from`: The channel members will get moved from
        """
        await self.move_all_members(ctx, channel_from, ctx.guild.afk_channel)

    async def move_all_members(self, ctx, channel_from: discord.VoiceChannel, channel_to: discord.VoiceChannel):
        member_amount = len(channel_from.members)
        if member_amount == 0:
            return await ctx.send(f"{channel_from.name} doesn't have any members in it.")
        # Check permissions to ensure a smooth transisition
        if channel_from.permissions_for(ctx.guild.me).move_members is False:
            return await ctx.send(f"I don't have permissions to move members in {channel_from.name}")
        if channel_to.permissions_for(ctx.guild.me).move_members is False:
            return await ctx.send(f"I don't have permissions to move members in {channel_to.name}")
        # Move the members
        """Internal function for massmoving, massmoves all members to the target channel"""
        for member in channel_from.members:
            try:
                await member.move_to(channel_to)
            except:
                pass
        await ctx.send(f"Done, massmoved {member_amount} members from **{channel_from.name}** to **{channel_to.name}**")
