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
from pydantic import BaseModel

from ..models import App
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

@service_router.get("/service/app/{app_id}")
async def register_app(app_id: str):
    data = App.get(app_id)

    if not data:
        return HTTPException(status_code=404, detail="App not found")
    
    return data.to_dict()