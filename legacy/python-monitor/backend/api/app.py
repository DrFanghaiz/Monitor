"""
FastAPI application — assembles routers and CORS middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes.status import router as status_router
from backend.api.routes.timer import router as timer_router
from backend.api.routes.statistics import router as statistics_router
from backend.api.routes.reservation import router as reservation_router
from backend.api.routes.settings import router as settings_router
from backend.api.routes.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="Monitor API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(status_router)
    app.include_router(timer_router)
    app.include_router(statistics_router)
    app.include_router(reservation_router)
    app.include_router(settings_router)
    app.include_router(auth_router)

    return app


app = create_app()
