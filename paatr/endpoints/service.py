"""
service.py
~~~~~~~~~~

This module contains the service endpoints for the API.
- Creating or deleting a service/application
- Registering a service/application
- Getting a service/application
- Getting all services/applications
"""

from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models import App
from ..helpers import repo_clone

# from ..decorators import auth_required

service_router = APIRouter()


class AppItem(BaseModel):
    name: str
    user_id: str
    description: Union[str, None] = None


@service_router.get("/")
async def hello():
    return {"hello": "world"}


@service_router.post("/service/app")
async def register_app(_app: AppItem):
    app = App(user_id=_app.user_id, name=_app.name, description=_app.description)
    data = app.register()

    if not data:
        raise ValueError("Failed to register app")

    return app.to_dict()


# @service_router.post("/uploadfile/")
# async def create_upload_file(files: list[UploadFile] | None = None):
#     if not files:
#         return {"message": "No upload file sent"}
#     return {"filename": [file.filename for file in files]}
#
# /repos/{owner}/{repo}/contents/{path}
@service_router.get("/repo_cloning/{git_url}")
async def git_clone(git_url: str, folder_name: str):
    """
        Upload the files for an application
        Args:
            git_url (str): The URL of the GitHub repository to be cloned
            folder_name (str): The name of the folder where the repo will be cloned

        Returns:
            JSONResponse
        """
    if not git_url:
        return HTTPException(status_code=409, detail="Missing Repository link to clone")
    if not folder_name:
        return HTTPException(status_code=409, detail="Folder name missing")
    if not await repo_clone(git_url, folder_name):
        return {"message": "Failed to clone Repo"}
    return JSONResponse(
        {
            "cloned": git_url,
            "location": folder_name
        }
    )


@service_router.get("/service/app/{app_id}")
async def register_app(app_id: str):
    data = App.get(app_id)
    if not data:
        return HTTPException(status_code=404, detail="App not found")

    return data.to_dict()
