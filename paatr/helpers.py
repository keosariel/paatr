from fastapi import Request
from fastapi.responses import JSONResponse


async def handle_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )