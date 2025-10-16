from __future__ import annotations
from typing import Dict, List, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from starlette import status

from app.schemas.common import Problem
from app.exceptions import ProblemException

def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(ProblemException)
    async def _problem_exc_handler(request: Request, exc: ProblemException):
        body = Problem(
            type=exc.type, title=exc.title, status=exc.status_code,
            detail=exc.detail, instance=str(request.url), errors=exc.errors,
        ).model_dump()
        return JSONResponse(body, status_code=exc.status_code, media_type="application/problem+json")

    @app.exception_handler(RequestValidationError)
    async def _request_validation_handler(request: Request, exc: RequestValidationError):
        # Flatten pydantic errors -> {field: [messages]}
        field_errors: Dict[str, List[str]] = {}
        for e in exc.errors():
            loc = [str(x) for x in e.get("loc", [])]
            # drop 'body'/'query'/'path' prefixes for brevity
            while loc and loc[0] in {"body", "query", "path"}:
                loc.pop(0)
            key = ".".join(loc) if loc else "non_field"
            field_errors.setdefault(key, []).append(e.get("msg", "invalid"))
        body = Problem(
            title="Invalid request",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request validation failed",
            instance=str(request.url),
            errors=field_errors or None,
        ).model_dump()
        return JSONResponse(body, status_code=422, media_type="application/problem+json")

    @app.exception_handler(IntegrityError)
    async def _integrity_handler(request: Request, exc: IntegrityError):
        # Best-effort message (unique/foreign key/constraint)
        msg = str(getattr(exc.orig, "args", [""])[0]) if getattr(exc, "orig", None) else str(exc)
        body = Problem(
            title="Conflict",
            status=status.HTTP_409_CONFLICT,
            detail=msg or "Constraint violation",
            instance=str(request.url),
        ).model_dump()
        return JSONResponse(body, status_code=409, media_type="application/problem+json")
