"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from typing import Union
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
    @commands.group(
        autohelp=False,
        invoke_without_command=True,
        usage="<from channel> <to channel>"
    )
    async def massmove(
        self,
        ctx,
        channel_from: Union[discord.VoiceChannel, discord.StageChannel],
        channel_to: Union[discord.VoiceChannel, discord.StageChannel]
    ):
        """Massmove members from one channel to another.

        This works the best if you enable Developer mode and copy the ID's for the channels.

        `from channel`: The channel members will get moved from
        `to channel`: The channel members will get moved to
        """
        await self.move_all_members(ctx, channel_from, channel_to)

    @checks.mod_or_permissions(move_members=True)
    @massmove.command(
        usage="<from channel>"
    )
    async def afk(self, ctx, channel_from: Union[discord.VoiceChannel, discord.StageChannel]):
        """Massmove members to the AFK channel

        This works the best if you enable Developer mode and copy the ID for the channel

        `from channel`: The channel members will get moved from
        """
        await self.move_all_members(ctx, channel_from, ctx.guild.afk_channel)

    @checks.mod_or_permissions(move_members=True)
    @massmove.command(
        usage="<to channel>"
    )
    async def me(self, ctx, channel_to: Union[discord.VoiceChannel, discord.StageChannel]):
        """Massmove you and every other member in the channel to another channel.

        This works the best if you enable Developer mode and copy the ID for the channel

        `to channel`: The channel members will get moved to
        """
        voice = ctx.author.voice
        if voice is None:
            return await ctx.send("You have to be in an voice channel to use this command.")
        await self.move_all_members(ctx, voice.channel, channel_to)

    async def move_all_members(self, ctx, channel_from: discord.VoiceChannel, channel_to: discord.VoiceChannel):
        plural = True
        member_amount = len(channel_from.members)
        if member_amount == 0:
            return await ctx.send(f"{channel_from.mention} doesn't have any members in it.")
        elif member_amount == 1:
            plural = False
        # Check permissions to ensure a smooth transisition
        if channel_from.permissions_for(ctx.guild.me).move_members is False:
            return await ctx.send(f"I don't have permissions to move members in {channel_from.mention}")
        if channel_to.permissions_for(ctx.guild.me).move_members is False:
            return await ctx.send(f"I don't have permissions to move members in {channel_to.mention}")
        # Move the members
        """Internal function for massmoving, massmoves all members to the target channel"""
        for member in channel_from.members:
            try:
                await member.move_to(channel_to)
            except:
                pass
        await ctx.send(
            f"Done, massmoved {member_amount} member{'s' if plural else ''} from **{channel_from.mention}** to **{channel_to.mention}**"
        )
