from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.user import User


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =====================================================
# INSCRIPTION
# =====================================================

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


# =====================================================
# CONNEXION - PAGE
# =====================================================

@router.get("/login")
async def login_page(request: Request):

    message = request.session.pop("message", None)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "message": message
        }
    )


# =====================================================
# CONNEXION - TRAITEMENT
# =====================================================

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

    # Mauvais identifiants
    if not user:

        request.session["message"] = (
            "❌ Téléphone ou mot de passe incorrect."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )


    # Créer la session
    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name

    # Message de connexion
    request.session["message"] = (
        "✅ Oups êtes maintenant connecté !"
    )

    return RedirectResponse(
        "/",
        status_code=303
    )


# =====================================================
# DÉCONNEXION
# =====================================================

@router.get("/logout")
async def logout(request: Request):

    request.session.clear()

    # Message après déconnexion
    request.session["message"] = (
        "✅ Oups êtes maintenant déconnecté."
    )

    return RedirectResponse(
        "/",
        status_code=303
    )