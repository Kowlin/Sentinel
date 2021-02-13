# In my opinion, this is a dumb idea, but its a sane dumb idea!
# Now amplified by Sinbad's ideas! NICE!


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
        }
    }"""

    findIssuePartialData = """issue-{number}: issueOrPullRequest(number: {number}) {
        __typename
        ... on PullRequest {
            number
            url
            repository {
                nameWithOwner
            }
        }
        ... on Issue {
            number
            url
            repository {
                nameWithOwner
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
            }
        }"""


class Mutations:
    """Prebuild GraphQL mutation calls"""
