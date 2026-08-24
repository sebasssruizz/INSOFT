"""Excepciones de negocio traducidas a respuestas HTTP en main.py."""


class ServiceError(Exception):
    status_code: int = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(ServiceError):
    status_code = 404


class ForbiddenError(ServiceError):
    status_code = 403


class ConflictError(ServiceError):
    status_code = 409


class BadRequestError(ServiceError):
    status_code = 400


class UnauthorizedError(ServiceError):
    status_code = 401
