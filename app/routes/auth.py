from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.user import User

from fastapi import Request

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

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )
@router.post("/login")
async def login_user(
    request: Request,
    phone: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    user = db.query(User).filter(
        User.phone == phone,
        User.password == password
    ).first()

    db.close()

    if not user:
        return RedirectResponse("/login", status_code=303)

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name

    return RedirectResponse("/", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()

    return RedirectResponse("/", status_code=303)
