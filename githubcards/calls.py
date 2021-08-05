# In my opinion, this is a dumb idea, but its a sane dumb idea!

"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


class Queries:
    """Prebuild GraphQL query calls"""

    validateUser = """
        query ValidateUser {
            viewer {
                id
                login
            }
            rateLimit {
                cost
                remaining
                limit
                resetAt
            }
        }"""

    validateRepo = """
        query ValidateRepo($repoOwner: String!, $repoName: String!) {
            repository(owner: $repoOwner, name: $repoName) {
                id
                name
            }
            rateLimit {
                cost
                remaining
                limit
                resetAt
            }
        }"""

    findIssueQuery = """query FindIssueOrPr {
        %(repositories)s
    }"""

    findIssueRepository = """repo%(idx)s: repository(owner: "%(owner)s", name: "%(repo)s") {
        %(issues)s
    }"""

    findIssueFullData = """issue%(number)s: issueOrPullRequest(number: %(number)s) {
        __typename
        ... on PullRequest {
            number
            title
            body
            url
            createdAt
            state
            mergeable
            isDraft
            milestone {
                title
            }
            author {
                login
                avatarUrl
                url
            }
            repository {
                nameWithOwner
            }
            labels(first:100) {
                nodes {
                    name
                }
            }
        }
        ... on Issue {
            number
            title
            body
            url
            createdAt
            state
            milestone {
                title
            }
            author {
                login
                avatarUrl
                url
            }
            repository {
                nameWithOwner
            }
            labels(first:100) {
                nodes {
                    name
                }
            }
        }
    }"""

    searchIssues = """
        query SearchIssues($query: String!) {
            search(type: ISSUE, query: $query, first: 15) {
                issueCount
                nodes {
                    __typename
                    ... on Issue {
                        state
                        number
                        title
                        url
                    }
                    ... on PullRequest {
                        mergeable
                        isDraft
                        state
                        number
                        title
                        url
                    }
                }
            }
            rateLimit {
                cost
                remaining
                limit
                resetAt
            }
        }"""


class Mutations:
    """Prebuild GraphQL mutation calls"""
