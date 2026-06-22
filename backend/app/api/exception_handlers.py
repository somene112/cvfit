"""Application-level exception handlers with stable public response shapes."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.billing.credit_gating import InsufficientCreditsError


async def insufficient_credits_handler(
    request: Request,
    exc: InsufficientCreditsError,
) -> JSONResponse:
    del request
    return JSONResponse(status_code=402, content=exc.response_body())
