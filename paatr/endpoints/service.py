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
from pydantic import BaseModel

from ..models import App
from .. import APP_FILES_DIR
from ..helpers import save_file, build_app, run_docker_image, get_image

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

@service_router.get("/service/app/{app_id}")
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


@service_router.post("/service/app/{app_id}/build")
async def build_app_(app_id: str):
    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")
    
    app_path = os.path.join(APP_FILES_DIR, app_data.name+".zip")
    
    return {"message": await build_app(app_path, app_data.name)}


@service_router.post("/service/app/{app_id}/run")
async def run_app(app_id: str):
    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")

    if not get_image(app_data.name):
        return {"message": "App has not been built"}
    
    await run_docker_image(app_data.name)

    