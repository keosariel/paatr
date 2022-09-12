import os
from fastapi import Request
from fastapi.responses import JSONResponse
from git import Repo


async def handle_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )


async def repo_clone(git_url: str, repo_dir: str) -> bool:
    if not os.path.exists(repo_dir):
        os.mkdir(repo_dir)
    try:
        os.chdir(repo_dir)
        rep = os.getcwd()
        Repo.clone_from(url=git_url, to_path=rep)
    except Exception as exc:
        return False
    return True
