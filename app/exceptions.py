from __future__ import annotations
from typing import Any, Mapping, Optional
from fastapi import status as http

class ProblemException(Exception):
    def __init__(
        self,
        status_code: int,
        title: str,
        *,
        detail: Optional[str] = None,
        type_: str = "about:blank",
        errors: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type = type_
        self.errors = errors or {}

class BadRequest(ProblemException):
    def __init__(self, detail: str = "Bad request", **kw: Any) -> None:
        super().__init__(http.HTTP_400_BAD_REQUEST, "Bad Request", detail=detail, **kw)

class Unauthorized(ProblemException):
    def __init__(self, detail: str = "Unauthorized", **kw: Any) -> None:
        super().__init__(http.HTTP_401_UNAUTHORIZED, "Unauthorized", detail=detail, **kw)

class Forbidden(ProblemException):
    def __init__(self, detail: str = "Forbidden", **kw: Any) -> None:
        super().__init__(http.HTTP_403_FORBIDDEN, "Forbidden", detail=detail, **kw)

class NotFound(ProblemException):
    def __init__(self, detail: str = "Not found", **kw: Any) -> None:
        super().__init__(http.HTTP_404_NOT_FOUND, "Not Found", detail=detail, **kw)

class Conflict(ProblemException):
    def __init__(self, detail: str = "Conflict", **kw: Any) -> None:
        super().__init__(http.HTTP_409_CONFLICT, "Conflict", detail=detail, **kw)

class Unprocessable(ProblemException):
    def __init__(self, detail: str = "Unprocessable", **kw: Any) -> None:
        super().__init__(http.HTTP_422_UNPROCESSABLE_ENTITY, "Unprocessable Entity", detail=detail, **kw)
