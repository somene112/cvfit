from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def ui_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})