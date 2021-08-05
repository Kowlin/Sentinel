"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Callable, Dict, Mapping, Optional

import aiohttp

from .calls import Queries
from .data import SearchData
from .exceptions import ApiError, Unauthorized

baseUrl = "https://api.github.com/graphql"
log = logging.getLogger("red.githubcards.http")


class RateLimit:
    """
    This is somewhat similar to what's in gidgethub.

    We really should just use that lib already...
    """

    def __init__(self, *, limit: int, remaining: int, reset: float, cost: Optional[int]) -> None:
        self.limit = limit
        self.remaining = remaining
        self.reset = reset
        self.cost = cost

    @classmethod
    def from_http(
        cls, headers: Mapping[str, Any], ratelimit_data: Mapping[str, Any]
    ) -> Optional[RateLimit]:
        try:
            limit = int(headers["x-ratelimit-limit"])
            remaining = int(headers["x-ratelimit-remaining"])
            reset = datetime.datetime.fromtimestamp(
                float(headers["x-ratelimit-reset"]), datetime.timezone.utc
            )
        except KeyError:
            try:
                limit = ratelimit_data["limit"]
                remaining = ratelimit_data["remaining"]
                reset = datetime.strptime(ratelimit_data["resetAt"], '%Y-%m-%dT%H:%M:%SZ')
            except KeyError:
                return None
        else:
            cost = ratelimit_data.get("cost")
            return cls(limit=limit, remaining=remaining, reset=reset, cost=cost)


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
            self._log_ratelimit(
                self.validate_user, call.headers, ratelimit_data=json['data']['rateLimit']
            )
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
            self._log_ratelimit(
                self.validate_repo, call.headers, ratelimit_data=json['data']['rateLimit']
            )
            return json

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
            self._log_ratelimit(
                self.search_issues, call.headers, ratelimit_data=json['data']['rateLimit']
            )
            search_results = json['data']['search']

            data = SearchData(
                total=search_results['issueCount'],
                results=search_results['nodes'],
                query=query
            )
            return data

    async def send_query(self, query: str):
        async with self.session.post(
            baseUrl,
            json={
                "query": query
            }
        ) as call:
            json = await call.json()
            self._log_ratelimit(self.send_query, call.headers)
            return json

    def _log_ratelimit(
        self,
        func: Callable[[...], Any],
        headers: Mapping[str, Any],
        *,
        ratelimit_data: Dict[str, Any] = {},
    ) -> None:
        ratelimit = RateLimit.from_http(headers, ratelimit_data)
        if ratelimit is not None:
            log.debug(
                "%s; cost %s, remaining: %s/%s",
                func.__name__,
                ratelimit.cost if ratelimit.cost is not None else "not provided",
                ratelimit.remaining,
                ratelimit.limit,
            )
        else:
            log.debug("%s; no RL data", func.__name__)
