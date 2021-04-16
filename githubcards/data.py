"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import quote_plus


@dataclass(init=True)
class SearchData(object):
    total: int  # data/search/issueCount
    results: list  # data/search/nodes
    query: str

    @property
    def escaped_query(self):
        return quote_plus(self.query)


@dataclass(init=True)
class IssueData(object):
    name_with_owner: str  # data/repository
    author_name: str  # data/issue/author
    author_url: str
    author_avatar_url: str
    issue_type: str
    number: int  # data/issue
    title: str
    url: str
    body_text: str
    state: str
    labels: Tuple[str, ...]
    created_at: datetime
    is_draft: Optional[bool] = None
    mergeable_state: Optional[str] = None
    milestone: Optional[str] = None


@dataclass(init=True)
class IssueStateColour(object):
    OPEN: int = 0x6cc644
    CLOSED: int = 0xbd2c00
    MERGED: int = 0x6e5494
