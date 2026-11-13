class AppError(Exception):
    code = "app_error"


class InvalidInputError(AppError):
    code = "invalid_input"


class NotFoundError(AppError):
    code = "not_found"


class ConflictError(AppError):
    code = "conflict"
