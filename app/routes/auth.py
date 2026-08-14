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
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    # Vérifier si le numéro existe déjà
    existing_user = (
        db.query(User)
        .filter(User.phone == phone)
        .first()
    )

    if existing_user:

        db.close()

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "❌ Ce numéro est déjà associé à un compte."
            }
        )

    # Créer le compte
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
        User.phone == phone
    ).first()

    print("================================")
    print("PHONE REÇU :", repr(phone))
    print("PASSWORD REÇU :", repr(password))

    if user:
        print("USER TROUVÉ :", user.id)
        print("PHONE DB :", repr(user.phone))
        print("PASSWORD DB :", repr(user.password))
    else:
        print("❌ AUCUN UTILISATEUR TROUVÉ")

    db.close()

    if not user:
        request.session["message"] = (
            "❌ Téléphone ou mot de passe incorrect."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )

    if user.password != password:

        print("❌ MOT DE PASSE INCORRECT")
        print("SAISI :", repr(password))
        print("DB   :", repr(user.password))

        request.session["message"] = (
            "❌ Téléphone ou mot de passe incorrect."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )

    print("✅ CONNEXION RÉUSSIE")

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name

    request.session["message"] = (
        "✅ Vous êtes maintenant connecté !"
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

    request.session["message"] = (
        "✅ Vous êtes maintenant déconnecté."
    )

    return RedirectResponse(
        "/",
        status_code=303
    )