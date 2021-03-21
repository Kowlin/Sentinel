"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import logging

import aiohttp

from .calls import Queries
from .data import SearchData
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

            return SearchData(
                total=search_results['issueCount'],
                results=search_results['nodes'],
                query=query
            )

    async def send_query(self, query: str):
        async with self.session.post(
            baseUrl,
            json={
                "query": query
            }
        ) as call:
            json = await call.json()
            log.debug(f"send_query; no RL data")
            return json
