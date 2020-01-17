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

    findIssue = """
        query FindIssueOrPr($repoName: String!, $repoOwner: String!, $issueID: Int!) {
            repository(owner: $repoOwner, name: $repoName) {
                issueOrPullRequest(number: $issueID) {
                    __typename
                    ... on PullRequest {
                       number
                        title
                        bodyText
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
                    }
                    ... on Issue {
                        number
                        title
                        bodyText
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
                    }
                }
            }
            rateLimit {
                cost
                remaining
                limit
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
