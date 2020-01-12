class RepoNotFound(Exception):
    pass


class ApiError(Exception):
    pass


class Unauthorized(ApiError):
    pass
