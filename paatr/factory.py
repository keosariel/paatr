from fastapi import FastAPI
from .endpoints import service_router
from .helpers import handle_errors
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    # Create the FastAPI application
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register the routers
    app.include_router(service_router)
    app.exception_handler(Exception)(handle_errors)
    return app