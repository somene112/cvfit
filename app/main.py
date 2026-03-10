from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.logging import configure_logging
from app.api.routes.health import router as health_router
from app.api.routes.cv import router as cv_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.ui import router as ui_router  # NEW

log = configure_logging()

app = FastAPI(title="CVFit API", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")  # NEW

app.include_router(health_router)
app.include_router(cv_router)
app.include_router(jobs_router)
app.include_router(ui_router)  # NEW