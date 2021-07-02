"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red

from .converters import RepoData
from .exceptions import ApiError, Unauthorized
from .formatters import FetchableReposDict, Formatters, Query
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


class OverflowButton(discord.ui.Button):
    def __init__(self, embeds: List[discord.Embed]) -> None:
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="See all linked issues",
        )
        self.embeds = embeds

    async def callback(self, interaction: discord.Interaction) -> None:
        issue_embeds = []
        overflow = []
        for index, issue in enumerate(self.embeds):
            if index < 8:
                issue_embeds.append(issue)
                continue
            else:
                overflow.append(f"[{issue.name_with_owner}#{issue.number}]({issue.url})")
                overflow_embed = discord.Embed(description=" • ".join(overflow))
                issue_embeds.append(overflow_embed)
        await interaction.response.send_message(
            embeds=issue_embeds,
            ephemeral=True
        )


class OverflowPersistentSelect(discord.ui.Select):
    def __init__(self, *, cog: GitHubCards, options: List[discord.SelectOption]) -> None:
        super().__init__(
            custom_id=f"kowlin/sentinel-{cog.bot.user.id}",
            placeholder="Show issue",
            options=options,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        fetchable_repos = {}
        if (matcher := self.cog.get_matcher_by_message(interaction.message)) is None:
            return fetchable_repos

        for item in self.values:
            self.cog.maybe_add_fetchable_issue(fetchable_repos, matcher, item)

        if fetchable_repos:
            await self.cog.query_and_post(
                message=None,
                fetchable_repos=fetchable_repos,
                interaction_response=interaction.response,
            )


class OverflowPersistentView(discord.ui.View):
    def __init__(
        self,
        *,
        cog: GitHubCards,
        options: List[discord.SelectOption] = discord.utils.MISSING,
        timeout: Optional[float] = None,
    ):
        super().__init__(timeout=timeout)
        persistent_select = OverflowPersistentSelect(cog=cog, options=options)
        self.add_item(persistent_select)


class OverflowView(OverflowPersistentView):
    def __init__(
        self,
        *,
        cog: GitHubCards,
        options: List[discord.SelectOption],
        embeds: List[discord.Embed],
    ) -> None:
        super().__init__(cog=cog, options=options, timeout=180.0)
        self.message: Optional[discord.Message] = None
        self.button = OverflowButton(embeds)
        self.add_item(self.button)

    async def on_timeout(self) -> None:
        if self.message is None:
            return
        self.remove_item(self.button)
        await self.message.edit(view=self)


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
        self.active_prefix_matchers = {}
        self.splitter = re.compile(r"[!?().,;:+|&/`\s]")
        self._ready = asyncio.Event()
        # assigned in initialize()
        self.http: GitHubAPI = None
        self.view = None

    async def initialize(self):
        """ cache preloading """
        await self.rebuild_cache_for_guild()
        await self._create_client()
        await self.bot.wait_until_red_ready()
        self.view = OverflowPersistentView(cog=self)
        self.bot.add_view(self.view)
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
                pattern = re.compile(rf"^({partial})#([0-9]+)$", re.IGNORECASE)
                self.active_prefix_matchers[int(guild_id)] = {"pattern": pattern, "data": guild_data}
        finally:
            self._ready.set()

    async def cog_before_invoke(self, ctx):
        await self._ready.wait()

    def cog_unload(self):
        if self.view is not None:
            self.view.stop()
        self.bot.loop.create_task(self.http.session.close())

    async def red_get_data_for_user(self, **kwargs):
        return {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    async def _get_token(self, api_tokens: Optional[Mapping[str, str]] = None) -> str:
        """Get GitHub token."""
        if api_tokens is None:
            api_tokens = await self.bot.get_shared_api_tokens("github")

        token = api_tokens.get("token", "")
        if not token:
            log.error("No valid token found")
        return token

    async def _create_client(self) -> None:
        """Create GitHub API client."""
        self.http = GitHubAPI(token=await self._get_token())

    @commands.guild_only()
    @commands.command(usage="<prefix> <search_query>")
    async def ghsearch(self, ctx, repo_data: RepoData, *, search_query: str):
        """Search for issues in GitHub repo.

        Protip: You can also search issues via ``prefix#s <search_query>``!"""
        async with ctx.channel.typing():
            search_data = await self.http.search_issues(
                repo_data["owner"], repo_data["repo"], search_query
            )
            embed = Formatters.format_search(search_data)
            await ctx.send(embed=embed)

    # Command groups
    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.group(aliases=["ghc"], name="githubcards")
    async def ghc_group(self, ctx):
        """GitHubCards settings."""

    @ghc_group.command(name="add")
    async def add(self, ctx, prefix: str, github_slug: str):
        """Add a new GitHub repository with the given prefix.

        Format for adding a new GitHub repo is "Username/Repository"
        """
        prefix = prefix.lower()  # Ensure lowering of prefixes, since fuck anything else.
        try:
            owner, repo = github_slug.split("/")
        except ValueError:
            await ctx.send('Invalid format. Please use ``Username/Repository``.')
            return

        try:
            await self.http.validate_repo(owner, repo)
        except ApiError:
            await ctx.send('The provided GitHub repository doesn\'t exist, or is unable to be accessed due to permissions.')
            return

        async with self.config.custom("REPO", ctx.guild.id).all() as repos:
            if prefix in repos.keys():
                await ctx.send('This prefix already exists in this server. Please use something else.')
                return

            repos[prefix] = {"owner": owner, "repo": repo}

        await self.rebuild_cache_for_guild(ctx.guild.id)
        await ctx.send(f"A GitHub repository (``{github_slug}``) added with a prefix ``{prefix}``")

    @ghc_group.command(name="remove", aliases=["delete"])
    async def remove(self, ctx, prefix: str):
        """Remove a GitHub repository with its given prefix.
        """
        await self.config.custom("REPO", ctx.guild.id, prefix).clear()
        await self.rebuild_cache_for_guild(ctx.guild.id)

        # if that prefix doesn't exist, it will still send same message but I don't care
        await ctx.send(f"A repository with the prefix ``{prefix}`` has been removed.")

    @ghc_group.command(name="list")
    async def list_prefixes(self, ctx):
        """List all prefixes for GitHub Cards in this server.
        """
        repos = await self.config.custom("REPO", ctx.guild.id).all()
        if not repos:
            await ctx.send("There are no configured GitHub repositories on this server.")
            return
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

    async def is_eligible_as_command(self, message: discord.Message) -> bool:
        """Check if message is eligible in command-like context."""
        return (
            self.http._token
            and not message.author.bot
            and message.guild is not None
            and await self.bot.message_eligible_as_command(message)
            and not await self.bot.cog_disabled_in_guild(self, message.guild)
        )

    def get_matcher_by_message(self, message: discord.Message) -> Optional[Dict[str, Any]]:
        """Get matcher from message object.

        This also checks if the message is eligible as command and returns None otherwise.
        """
        return self.active_prefix_matchers.get(message.guild.id)

    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ):
        """Update GitHub token when `[p]set api` command is used."""
        if service_name != "github":
            return
        await self.http.recreate_session(await self._get_token(api_tokens))

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        await self._ready.wait()

        if not await self.is_eligible_as_command(message):
            return

        # --- MODULE FOR SEARCHING! ---
        # JSON is cached right... so this should be fine...
        # If I really want to *enjoy* this... probs rework this into a pseudo command module
        guild_data = await self.config.custom("REPO", message.guild.id).all()
        for prefix, data in guild_data.items():
            if message.content.startswith(f"{prefix}#s "):
                async with message.channel.typing():
                    search_query = message.content.replace(f"{prefix}#s ", "")
                    search_data = await self.http.search_issues(
                        data["owner"], data["repo"], search_query
                    )
                    embed = Formatters.format_search(search_data)
                    await message.channel.send(embed=embed)
                    return

        # --- MODULE FOR GETTING EXISTING PREFIXES ---
        fetchable_repos = self.get_fetchable_repos(message)

        if not fetchable_repos:
            return  # End if no repos are found to query over.

        async with message.channel.typing():
            await self.query_and_post(message, fetchable_repos)

    def get_fetchable_repos(self, message) -> dict:
        fetchable_repos: Dict[Tuple[str, str], FetchableReposDict] = {}

        if (matcher := self.get_matcher_by_message(message)) is None:
            return fetchable_repos

        for item in self.splitter.split(message.content):
            self.maybe_add_fetchable_issue(fetchable_repos, matcher, item)

        return fetchable_repos

    def maybe_add_fetchable_issue(self, fetchable_repos: dict, matcher, item: str) -> None:
        match = matcher["pattern"].match(item)
        if match is None:
            return
        prefix = match.group(1).lower()
        number = int(match.group(2))

        prefix_data = matcher["data"][prefix]
        name_with_owner = (prefix_data['owner'], prefix_data['repo'])

        # Magical fetching aquesition done.
        # Ensure that the repo exists as a key
        if name_with_owner not in fetchable_repos:
            fetchable_repos[name_with_owner] = {
                "owner": prefix_data["owner"],
                "repo": prefix_data["repo"],
                "prefix": prefix,
                "fetchable_issues": set()
            }
        # No need to post card for same issue number from the same repo in one message twice
        if number in fetchable_repos[name_with_owner]['fetchable_issues']:
            return
        fetchable_repos[name_with_owner]['fetchable_issues'].add(number)

    async def query_and_post(self, message, fetchable_repos, *, interaction_response=None):
        # --- FETCHING ---
        query = Query.build_query(fetchable_repos)
        try:
            query_data = await self.http.send_query(query.query_string)
        except Unauthorized:
            log.error("The current GitHub token is invalid.")
            return
            # Lmao what's error handling

        issue_data_list = []
        for repo_data in query_data["data"].values():
            for issue_data in repo_data.values():
                if issue_data is not None:
                    issue_data_list.append(Formatters.format_issue_class(issue_data))

        if not issue_data_list:
            # Fetching of all issues has failed somehow. So end it here.
            return

        # --- SENDING ---
        issue_embeds = []
        overflow = []
        overflow_embeds = []
        overflow_options = []

        for index, issue in enumerate(issue_data_list):
            if index < 1:
                e = Formatters.format_issue(issue)
                issue_embeds.append(e)
                continue
            else:
                e = Formatters.format_issue(issue)
                overflow.append(f"[{issue.name_with_owner}#{issue.number}]({issue.url})")
                prefix = fetchable_repos[tuple(issue.name_with_owner.split("/"))]["prefix"]
                # TODO: account for the Select option and char limit
                overflow_options.append(
                    discord.SelectOption(
                        label=f"{prefix}#{issue.number}",
                        description=(
                            issue.title[:49] + "\N{HORIZONTAL ELLIPSIS}"
                            if len(issue.title) > 50
                            else issue.title
                        ),
                    )
                )
                overflow_embeds.append(e)

        if interaction_response is not None:
            await interaction_response.send_message(embeds=issue_embeds, ephemeral=True)
            return

        view = None
        if overflow:
            embed = discord.Embed()
            embed.description = " • ".join(overflow)
            view = OverflowView(cog=self, embeds=overflow_embeds, options=overflow_options)
            issue_embeds.append(embed)

        new_message = await message.channel.send(embeds=issue_embeds, view=view)
        if overflow:
            view.message = new_message
