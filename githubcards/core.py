import discord
import aiohttp
import asyncio
import logging
import re

from dataclasses import dataclass
from typing import Optional, Union
from redbot import VersionInfo, version_info as red_version
from redbot.core import checks, commands, Config

from .calls import Queries, Mutations
from .data import SearchData, IssueData
from .exceptions import ApiError, RepoNotFound
from .http import GitHubAPI

log = logging.getLogger("red.githubcards.core")


"""
{
    "prefix slug": {
        "owner": "Cog-Creators",
        "repo": "Red-DiscordBot",
    }
}
"""


class GitHubCards(commands.Cog):
    """GitHub Cards"""
    # Oh my god I'm doing it

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25360017)
        self.config.init_custom("REPO", 2)
        self.config.register_custom(
            "REPO",  # + 2 identifiers: (guild_id, prefix)
            owner=None,
            repo=None,
        )
        self.active_prefix_matcherers = {}
        self._ready = asyncio.Event()
        self._startup_task = asyncio.create_task(self.get_ready())

        self.stateColours = {  # Can't be bothered to do this properly ATM
            'OPEN': 0x6cc644,
            'CLOSED': 0xbd2c00,
            'MERGED': 0x6e5494
        }

    async def get_ready(self):
        """ cache preloading """
        await self.rebuild_cache_for_guild()
        await self._set_token()
        self._ready.set()

    async def rebuild_cache_for_guild(self, *guild_ids):
        self._ready.clear()
        try:
            repos = await self.config.custom("REPO").all()
            data = {int(k): v for k, v in repos.items()}
            if guild_ids:
                data = {k: v for k, v in data.items() if k in guild_ids}

            for guild_id, guild_data in data.items():
                partial = "|".join(re.escape(prefix) for prefix in guild_data.keys())
                pattern = re.compile(
                    rf"(?:\s|^)({partial})#([0-9]+)(?:[\s,.]|$)",
                    re.IGNORECASE | re.MULTILINE,
                )
                self.active_prefix_matcherers[int(guild_id)] = {"pattern": pattern, "data": guild_data}
        finally:
            self._ready.set()

    async def cog_before_invoke(self, ctx):
        await self._ready.wait()

    def cog_unload(self):
        try:
            self.http.session.detach()
        except AttributeError:
            pass

    async def _set_token(self) -> bool:
        """Get the token and prepare the header"""
        try:  # Legacy edition
            github_keys = await self.bot.db.api_tokens.get_raw("github", default={"token": None})
        except AttributeError:
            github_keys = await self.bot.get_shared_api_tokens("github")

        if github_keys.get("token") is None:
            log.error("No valid token found")
            return False
        self.http = GitHubAPI(token=github_keys["token"])
        return True

    # Command groups
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group(aliases=["ghc"], name="githubcards")
    async def ghc_group(self, ctx):
        pass

    @ghc_group.command(name="add")
    async def add(self, ctx, prefix: str, github_slug: str):
        """Add a new GitHub repository with the given prefix.

        Format for adding a new GitHub repo is "Username/Repository"
        """
        prefix = prefix.lower()  # Ensure lowering of prefixes, since fuck anything else.
        try:
            owner, repo = github_slug.split("/")
        except ValueError:
            await ctx.send('Invalid format. Please use Username/Repository')
            return

        async with self.config.custom("REPO", ctx.guild.id).all() as repos:
            if prefix in repos.keys():
                await ctx.send('This prefix already exists in this server. Please use something else.')
                return

            repos[prefix] = {"owner": owner, "repo": repo}

        await self.rebuild_cache_for_guild(ctx.guild.id)
        await ctx.send(f"A GitHub repository ``{github_slug}`` added with a prefix ``{prefix}``")

    @ghc_group.command(name="remove", aliases=["delete"])
    async def remove(self, ctx, prefix: str):
        """Remove a GitHub repository with its given prefix.
        """
        await self.config.custom("REPO", ctx.guild.id, prefix).clear()
        await self.rebuild_cache_for_guild(ctx.guild.id)

        # if that prefix doesn't exist, it will still send same message but I don't care
        await ctx.send(f"A repository with the prefix ``{prefix}`` removed.")

    @ghc_group.command(name="list")
    async def list_prefixes(self, ctx):
        """List all prefixes for GitHub Cards in this server.
        """
        repos = await self.config.custom("REPO", ctx.guild.id).all()
        if not repos:
            await ctx.send("There are no configured prefixes on this server.")
            return
        # not the most readable code I wrote :P
        # You don't say ~ Kowlin
        msg = "\n".join(
            f"``{prefix}``: ``{repo['owner']}/{repo['repo']}``" for prefix, repo in repos.items()
        )
        await ctx.send(f"List of configured prefixes on **{ctx.guild.name}** server:\n{msg}")

    @ghc_group.command(name="instructions")
    async def instructions(self, ctx):
        """Learn on how to setup GHC

        *This will be the first time that someone will ACTUALLY read instructions*"""
        message = """
Begin by creating a new personal token on your GitHub Account here;
<https://github.com/settings/tokens>

If you do not trust this to your own account, its recommended you make a new GitHub account to act for the bot.
No additional permissions are required for public repositories, if you want to fetch from private repositories, you require full "repo" permissions.

Copy your newly created token and go to your DMs with the bot, and run the following command.
``[p]set api github token [YOUR NEW TOKEN]``

Finally reload the cog with ``[p]reload githubcards`` and you're set to add in new prefixes.
"""
        await ctx.send(message)

    def format_search(self, search_data: SearchData) -> discord.Embed:
        """Format the search results into an embed"""
        embed = discord.Embed()
        embed_body = ""
        for entry in search_data.results:
            embed_body += f"[[{entry['number']}]({entry['url']})] {entry['title']}\n"
        if search_data.total > 15:
            embed.set_footer(text=f"Showing the first 15 results, {search_data.total} results in total.")
            embed_body += f"\n\n[Click here for all the results](https://github.com/search?type=Issues&q={search_data.query})"
        embed.description = embed_body
        return embed

    def format_issue(self, issue_data: IssueData) -> discord.Embed:
        """Format a single issue into an embed"""
        embed = discord.Embed()
        embed.set_author(
            name=issue_data.author_name,
            url=issue_data.author_url,
            icon_url=issue_data.author_avatar_url
        )
        embed.title = f"{issue_data.title} #{issue_data.number}"
        embed.url = issue_data.url
        embed.description = issue_data.body_text[:300]
        embed.colour = self.stateColours[issue_data.state]
        formatted_datetime = issue_data.created_at.strftime('%d %b %Y, %H:%M')
        embed.set_footer(text=f"Created on {formatted_datetime}")
        # let's ignore this for now, since we want this to be compact, *fun*
        # embed.add_field(name=f"Labels [{len(issue_data.labels)}]", value=", ".join(issue_data.labels))
        if issue_data.mergeable_state is not None and issue_data.state == "OPEN":
            embed.add_field(name="Merge Status", value=issue_data.mergeable_state.capitalize())
        if issue_data.milestone:
            embed.add_field(name="Milestone", value=issue_data.milestone)
        return embed

    async def version_safe_allowed(self, who: discord.Member):
        if red_version >= VersionInfo.from_str("3.2.0"):
            return await self.bot.allowed_by_whitelist_blacklist(who)
        else:

            guild = who.guild

            if await self.bot.is_owner(who):
                return True

            global_whitelist = await self.bot.db.whitelist()
            if global_whitelist:
                if who.id not in global_whitelist:
                    return False
            else:
                # blacklist is only used when whitelist doesn't exist.
                global_blacklist = await self.bot.db.blacklist()
                if who.id in global_blacklist:
                    return False

            ids = {i for i in (who.id, *(who._roles)) if i != guild.id}

            guild_whitelist = await self.bot.db.guild(guild).whitelist()
            if guild_whitelist:
                if ids.isdisjoint(guild_whitelist):
                    return False
            else:
                guild_blacklist = await self.bot.db.guild(guild).blacklist()
                if not ids.isdisjoint(guild_blacklist):
                    return False

            return True

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        await self._ready.wait()
        if not self.http:
            if not await self._set_token():
                return
        if message.author.bot:
            return
        guild = message.guild
        if guild is None:
            return  # End the function here if its anything but a guild.
        if not await self.version_safe_allowed(message.author):
            return  # There, version safe allowed func in.

        cache = self.active_prefix_matcherers.get(guild.id, None)
        if not cache:
            return

        for match in cache["pattern"].finditer(message.content):
            prefix = match.group(1)
            number = int(match.group(2))
            # hey, you're the one who wanted to add search queries
            # now we have to figure out regex for that :aha:
            # or write a DSL parser (simple™)
            prefix_data = cache["data"][prefix.lower()]
            owner, repo = prefix_data['owner'], prefix_data['repo']
            try:
                issue_data = await self.http.find_issue(owner, repo, number)
            except ApiError as e:
                # possibly log
                if e.args[0][0]["type"] == "NOT_FOUND":
                    log.debug(f"Issue with number {number} on repo {owner}/{repo} couldn't be found")
                    return
                else:
                    raise
            embed = self.format_issue(issue_data)
            await message.channel.send(embed=embed)
