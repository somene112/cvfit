from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.api.routes.health import router as health_router
from app.api.routes.cv import router as cv_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.ui import router as ui_router

log = configure_logging()
init_db()

app = FastAPI(title="CVFit API", version="0.2.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health_router)
app.include_router(cv_router)
app.include_router(jobs_router)
app.include_router(ui_router)