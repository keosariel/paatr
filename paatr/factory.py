from fastapi import FastAPI
from .endpoints import auth_router, service_router
from .helpers import handle_errors

def create_app():
    # Create the FastAPI application
    app = FastAPI()

    # Register the routers
    app.include_router(auth_router)
    app.include_router(service_router)

    app.exception_handler(Exception)(handle_errors)
    return app