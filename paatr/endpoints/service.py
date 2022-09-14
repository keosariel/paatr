"""
service.py
~~~~~~~~~~

This module contains the service endpoints for the API.
- Creating or deleting a service/application
- Registering a service/application
- Getting a service/application
- Getting all services/applications
"""
import os
from typing import Union

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models import App
from .. import APP_FILES_DIR
from ..helpers import (save_file, build_app, run_docker_image, 
                        get_image, get_container)

service_router = APIRouter()

class AppItem(BaseModel):
    name: str
    user_id: str
    description: Union[str, None] = None

class BuildItem(BaseModel):
    username: str
    gh_token: str

@service_router.get("/")
async def hello():
    return {"hello": "world"}

@service_router.post("/services/apps")
async def register_app(_app: AppItem):
    """
    Register a new application

    Args:
        _app (AppItem): The application data
    
    Returns:
        dict: The application data
    """
    app = App(user_id=_app.user_id, name=_app.name, description=_app.description)
    data = app.register()

    if not data:
        raise ValueError("Failed to register app")

    return app.to_dict()

@service_router.get("/services/apps/{app_id}")
async def register_app(app_id: str):
    """
    Retrieve an application data

    Args:
        app_id (str): The ID of the application
    
    Returns:
        dict: The application data
    """
    data = App.get(app_id)

    if not data:
        return HTTPException(status_code=404, detail="App not found")
    
    return data.to_dict()

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
    
    return {
            "cloned": git_url,
            "location": folder_name
        }

@service_router.post("/service/app/{app_id}/upload")
async def app_files(app_id: str, file: UploadFile):
    """
    Upload the files for an application

    Args:
        app_id (str): The ID of the application
        file (UploadFile): The file to upload
    
    Returns:
        dict: The file data
    """
    app_data = App.get(app_id)

    if not app_data:
        return HTTPException(status_code=404, detail="App not found")
    
    if not file:
        return {"message": "No file sent"}

    if file.content_type != "application/zip":
        return {"message": "File is not a zip file"}

    contents = await file.read()
    
    if not await save_file(app_data.name+".zip", APP_FILES_DIR, contents):
        return {"message": "Failed to save app content"}
    
    return {"filename": file.filename, "fileb_content_type": file.content_type}


@service_router.post("/services/apps/{app_id}/build")
async def build_app_(app_id: str, build_data: BuildItem):
    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")
    
    repo = app_data.repo
    # github_url = repo["git_url"].replace("git://", f"https://{build_data.username}:{build_data.gh_token}@")
    github_url = repo["git_url"].replace("git://", f"https://")

    return {"message": await build_app(github_url, app_data.name)}


@service_router.post("/services/apps/{app_id}/run")
async def run_app(app_id: str):
    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")

    if not get_image(app_data.name):
        return {"message": "App has not been built"}
    
    await run_docker_image(app_data.name)

@service_router.get("/services/apps/{app_id}/status")
async def app_status(app_id: str):
    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")

    if not get_image(app_data.name):
        return {"message": "App has not been built", "status": "not-built"}

    if not get_container(app_data.name):
        return {"message": "App is not running", "status": "not-running"}

    return {"message": "App is running", "status": "running"}