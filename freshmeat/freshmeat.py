import discord

from redbot.core import commands
from redbot.core import checks
from redbot.core.utils.chat_formatting import pagify, escape
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

import datetime

BaseCog = getattr(commands, "Cog", object)


class Freshmeat(BaseCog):

    def __init__(self, bot):
        self.bot = bot

    async def red_get_data_for_user(self, **kwargs):
        return {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(kick_members=True)
    async def freshmeat(self, ctx, hours: int = 24):
        """Show the members who joined in the specified timeframe

        `hours`: A number of hours to check for new members, must be above 0"""
        if hours < 1:
            return await ctx.send("Consider putting hours above 0. Since that helps with searching for members. ;)")
        elif hours > 300:
            return await ctx.send("Please use something less then 300 hours.")

        member_list = []
        for member in ctx.guild.members:
            if member.joined_at > ctx.message.created_at - datetime.timedelta(hours=hours):
                member_list.append([member.display_name, member.id, member.joined_at])

        member_list.sort(key=lambda member: member[2], reverse=True)
        member_string = ""
        for member in member_list:
            member_string += f"\n{member[0]} ({member[1]})"

        pages = []
        for page in pagify(escape(member_string, formatting=True), page_length=1000):
            embed = discord.Embed(description=page)
            embed.set_author(
                name=f"{ctx.author.display_name}'s freshmeat of the day.",
                icon_url=ctx.author.avatar_url_as(format="png")
            )
            pages.append(embed)

        page_counter = 1
        for page in pages:
            page.set_footer(text=f"Page {page_counter} out of {len(pages)}")
            page_counter += 1

        await menu(
            ctx,
            pages=pages,
            controls=DEFAULT_CONTROLS,
            message=None,
            page=0,
            timeout=90
        )
