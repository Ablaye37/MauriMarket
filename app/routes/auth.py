from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.user import User


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/register")
async def register_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@router.post("/register")
async def register_user(
    full_name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    user = User(
        full_name=full_name,
        phone=phone,
        password=password
    )

    db.add(user)
    db.commit()
    db.close()

    return RedirectResponse(
        "/login",
        status_code=303
    )
