import os
from typing import Union

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel

from ..models import App
from ..helpers import (get_app_status, build_app, run_docker_image, 
                        get_image)
from .. import logger, ALL_APPS_LOGS_CACHE


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
    logger.info("Hello World!")
    return {"hello": "world"}

@service_router.get("/services/apps/{app_id}")
async def get_app_data(app_id: str):
    """
    Retrieve an application data

    Args:
        app_id (str): The ID of the application
    
    Returns:
        dict: The application data
    """
    logger.info("Getting app data for %s", app_id)

    data = App.get(app_id)

    if not data:
        return HTTPException(status_code=404, detail="App not found")
    
    return data.to_dict()

@service_router.post("/services/apps/{app_id}/build")
async def build_app_(app_id: str, build_data: BuildItem):
    """
    Build an application

    Args:
        app_id (str): The ID of the application
        build_data (BuildItem): The build data
    
    Returns:
        dict: The application data
    """
    logger.info("Building app %s", app_id)

    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")
    
    repo = app_data.repo
    # github_url = repo["git_url"].replace("git://", f"https://{build_data.username}:{build_data.gh_token}@")
    github_url = repo["git_url"].replace("git://", f"https://")

    # TODO: Run this in the background
    await build_app(github_url, app_data.name)

    return get_app_status(app_data.name)


@service_router.post("/services/apps/{app_id}/run")
async def run_app(app_id: str):
    """
    Run an application

    Args:
        app_id (str): The ID of the application

    Returns:
        dict: The application data
    """
    logger.info("Running app %s", app_id)

    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")

    if not get_image(app_data.name):
        return {"message": "App has not been built"}
    
    # TODO: Run this in the background
    await run_docker_image(app_data.name, app_data.id)

    return get_app_status(app_data.name)

@service_router.get("/services/apps/{app_id}/status")
async def app_status(app_id: str):
    app_data = App.get(app_id)
    
    if not app_data:
        return HTTPException(status_code=404, detail="App not found")

    return get_app_status(app_data.name)