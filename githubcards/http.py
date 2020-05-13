import logging
from datetime import datetime

import aiohttp

from .calls import Queries
from .data import SearchData, IssueData
from .exceptions import ApiError, Unauthorized

baseUrl = "https://api.github.com/graphql"
log = logging.getLogger("red.githubcards.http")


class GitHubAPI:
    def __init__(self, token: str) -> None:
        self.session: aiohttp.ClientSession
        self._token: str
        self._create_session(token)

    async def recreate_session(self, token: str) -> None:
        await self.session.close()
        self._create_session(token)

    def _create_session(self, token: str) -> None:
        headers = {
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.shadow-cat-preview+json",
        }
        self._token = token
        self.session = aiohttp.ClientSession(headers=headers)

    async def validate_user(self):
        async with self.session.post(baseUrl, json={"query": Queries.validateUser}) as call:
            json = await call.json()
            if call.status == 401:
                raise Unauthorized(json["message"])
            if "errors" in json.keys():
                raise ApiError(json['errors'])
            ratelimit = json['data']['rateLimit']
            log.debug(f"validate_user; cost {ratelimit['cost']}, remaining; {ratelimit['remaining']}/{ratelimit['limit']}")
            return json

    async def validate_repo(self, repoOwner: str, repoName: str):
        async with self.session.post(
            baseUrl,
            json={
                "query": Queries.validateRepo,
                "variables": {"repoOwner": repoOwner, "repoName": repoName},
            },
        ) as call:
            json = await call.json()
            if call.status == 401:
                raise Unauthorized(json["message"])
            if "errors" in json.keys():
                raise ApiError(json['errors'])
            ratelimit = json['data']['rateLimit']
            log.debug(f"validate_repo; cost {ratelimit['cost']}, remaining; {ratelimit['remaining']}/{ratelimit['limit']}")
            return json

    async def find_issue(self, repoOwner: str, repoName: str, issueID: int):
        async with self.session.post(
            baseUrl,
            json={
                "query": Queries.findIssue,
                "variables": {"repoOwner": repoOwner, "repoName": repoName, "issueID": issueID},
            },
        ) as call:
            json = await call.json()
            if call.status == 401:
                raise Unauthorized(json["message"])
            if "errors" in json.keys():
                raise ApiError(json['errors'])
            ratelimit = json['data']['rateLimit']
            issue = json['data']['repository']['issueOrPullRequest']
            log.debug(f"find_issue; cost {ratelimit['cost']}, remaining; {ratelimit['remaining']}/{ratelimit['limit']}")

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
                    "avatarUrl": "https://avatars2.githubusercontent.com/u/10137?u=b1951d34a583cf12ec0d3b0781ba19be97726318&v=4"
                }

            data = IssueData(
                ratelimit_remaining=ratelimit['remaining'],
                ratelimit_limit=ratelimit['limit'],
                ratelimit_cost=ratelimit['cost'],
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
                created_at=datetime.strptime(issue['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
            )
            return data

    async def search_issues(self, repoOwner: str, repoName: str, searchParam: str):
        query = f"repo:{repoOwner}/{repoName} {searchParam}"
        async with self.session.post(
            baseUrl,
            json={
                "query": Queries.searchIssues,
                "variables": {"query": query}
            }
        ) as call:
            json = await call.json()
            if "errors" in json.keys():
                raise ApiError(json['errors'])
            ratelimit = json['data']['rateLimit']
            search_results = json['data']['search']
            log.debug(f"search_issues; cost {ratelimit['cost']}, remaining; {ratelimit['remaining']}/{ratelimit['limit']}")

            data = SearchData(
                ratelimit_remaining=ratelimit['remaining'],
                ratelimit_limit=ratelimit['limit'],
                ratelimit_cost=ratelimit['cost'],
                total=search_results['issueCount'],
                results=search_results['nodes'],
                query=query
            )
            return data
