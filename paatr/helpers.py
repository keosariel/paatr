import os

from fastapi import Request
from fastapi.responses import JSONResponse


async def handle_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

async def save_file(filename, dir_path, contents, _mode="wb"):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    try:
        with open(os.path.join(dir_path, filename), _mode) as fp:
            fp.write(contents)
    except Exception as e:
        return False
    
    return True