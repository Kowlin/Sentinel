"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import discord
from redbot.core.utils.chat_formatting import pagify

from datetime import datetime
from typing import Dict, List, TypedDict

from .data import IssueData, SearchData, IssueStateColour
from .calls import Queries


class Formatters:
    @staticmethod
    def format_issue_class(issue: dict) -> IssueData:
        mergeable_state = issue.get("mergeable", None)
        is_draft = issue.get("isDraft", None)
        milestone = issue["milestone"]
        if milestone is not None:
            milestone_title = milestone["title"]
        else:
            milestone_title = None

        if issue['author'] is None:
            issue['author'] = {
                "login": "Ghost",
                "url": "https://github.com/ghost",
                "avatarUrl": "https://avatars.githubusercontent.com/u/10137?v=4"
            }
        labels = tuple(label["name"] for label in issue["labels"]["nodes"])

        data = IssueData(
            name_with_owner=issue['repository']['nameWithOwner'],
            author_name=issue['author']['login'],
            author_url=issue['author']['url'],
            author_avatar_url=issue['author']['avatarUrl'],
            issue_type=issue['__typename'],
            number=issue['number'],
            title=issue['title'],
            body_text=issue['body'],
            url=issue['url'],
            state=issue['state'],
            is_draft=is_draft,
            mergeable_state=mergeable_state,
            milestone=milestone_title,
            labels=labels,
            created_at=datetime.strptime(issue['createdAt'], '%Y-%m-%dT%H:%M:%S%z')
        )
        return data

    @staticmethod
    def format_issue(issue_data: IssueData) -> discord.Embed:
        """Format a single issue into an embed"""
        embed = discord.Embed()
        embed.set_author(
            name=issue_data.author_name,
            url=issue_data.author_url,
            icon_url=issue_data.author_avatar_url
        )
        number_suffix = f" #{issue_data.number}"
        max_len = 256 - len(number_suffix)
        if len(issue_data.title) > max_len:
            embed.title = f"{issue_data.title[:max_len-3]}...{number_suffix}"
        else:
            embed.title = f"{issue_data.title}{number_suffix}"
        embed.url = issue_data.url
        if len(issue_data.body_text) > 300:
            embed.description = next(pagify(issue_data.body_text, delims=[" ", "\n"], page_length=300, shorten_by=0)) + "..."
        else:
            embed.description = issue_data.body_text
        embed.colour = getattr(IssueStateColour, issue_data.state)
        if issue_data.labels:
            embed.add_field(
                name=f"Labels [{len(issue_data.labels)}]",
                value=", ".join(issue_data.labels[:5]),
            )
        if issue_data.mergeable_state is not None and issue_data.state == "OPEN":
            mergable_state = issue_data.mergeable_state.capitalize()
            if issue_data.is_draft is True:
                mergable_state = "Drafted"
            embed.add_field(name="Merge Status", value=mergable_state)
        if issue_data.milestone:
            embed.add_field(name="Milestone", value=issue_data.milestone)    
        formatted_datetime = f"<t:{int(issue_data.created_at.timestamp())}:f>"
        embed.add_field(
            name="\u200b",
            value=f"{issue_data.name_with_owner} • Created on {formatted_datetime}",
            inline=False,
        )
        return embed

    @staticmethod
    def format_search(search_data: SearchData) -> discord.Embed:
        """Format the search results into an embed"""
        embed = discord.Embed()
        embed_body = ""
        if not search_data.results:
            embed.description = "Nothing found."
            return embed
        for entry in search_data.results[:10]:
            if entry["state"] == "OPEN":
                state = "\N{LARGE GREEN CIRCLE}"
            elif entry["state"] == "CLOSED":
                state = "\N{LARGE RED CIRCLE}"
            else:
                state = "\N{LARGE PURPLE CIRCLE}"

            issue_type = (
                "Issue"
                if entry["__typename"] == "Issue"
                else "Pull Request"
            )
            mergeable_state = entry.get("mergeable", None)
            is_draft = entry.get("isDraft", None)
            if entry["state"] == "OPEN":
                if is_draft is True:
                    state = "\N{PENCIL}\N{VARIATION SELECTOR-16}"
                elif mergeable_state == "CONFLICTING":
                    state = "\N{WARNING SIGN}\N{VARIATION SELECTOR-16}"
                elif mergeable_state == "UNKNOWN":
                    state = "\N{WHITE QUESTION MARK ORNAMENT}"
            embed_body += (
                f"\n{state} - **{issue_type}** - **[#{entry['number']}]({entry['url']})**\n"
                f"{entry['title']}"
            )
        if search_data.total > 10:
            embed.set_footer(text=f"Showing the first 10 results, {search_data.total} results in total.")
            embed_body += (
                "\n\n[Click here for all the results]"
                f"(https://github.com/search?type=Issues&q={search_data.escaped_query})"
            )
        embed.description = embed_body
        return embed


class FetchableReposDict(TypedDict):
    owner: str
    repo: str
    prefix: str
    fetchable_issues: Dict[int, None]


class Query:
    def __init__(self, query_string: str, repos: List[FetchableReposDict]):
        self.query_string = query_string
        self.repos = repos

    @classmethod
    def build_query(cls, fetchable_repos: Dict[str, FetchableReposDict]) -> str:
        repo_queries = []
        repos = list(fetchable_repos.values())
        for idx, repo_data in enumerate(repos):
            issue_queries = []
            for issue in repo_data['fetchable_issues']:
                issue_queries.append(Queries.findIssueFullData % {"number": issue})
            repo_queries.append(
                Queries.findIssueRepository
                % {
                    "idx": idx,
                    "owner": repo_data["owner"],
                    "repo": repo_data["repo"],
                    "issues": "\n".join(issue_queries),
                }
            )

        query_string = Queries.findIssueQuery % {"repositories": "\n".join(repo_queries)}

        return cls(query_string, repos)
