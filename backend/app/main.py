from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.logging import configure_logging
from app.core.config import resolve_path, settings, validate_runtime_config
from app.core.cors import add_cors_middleware
from app.db.init_db import init_db
from app.api.routes.health import router as health_router
from app.api.routes.cv import router as cv_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.ui import router as ui_router
from app.api.routes.applications import router as applications_router
from app.api.routes.profile import router as profile_router
from app.api.routes.target_jobs import router as target_jobs_router
from app.api.routes.learning import router as learning_router, target_job_router as learning_target_job_router
from app.api.routes.interview_sessions import router as interview_sessions_router
from app.api.routes.help_assistant import router as help_assistant_router
from app.api.routes.share_links import router as share_links_router, public_router as share_public_router

log = configure_logging()
validate_runtime_config()
init_db()

app = FastAPI(title="CVFit API", version="0.2.0")
add_cors_middleware(app)
app.mount("/static", StaticFiles(directory=resolve_path(settings.FRONTEND_STATIC_DIR)), name="static")

app.include_router(health_router)
app.include_router(cv_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(ui_router)
app.include_router(applications_router)
app.include_router(profile_router)
app.include_router(target_jobs_router)
app.include_router(learning_router)
app.include_router(learning_target_job_router)
app.include_router(interview_sessions_router)
app.include_router(help_assistant_router)
app.include_router(share_links_router)
app.include_router(share_public_router)
