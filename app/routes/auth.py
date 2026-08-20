from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.user import User
from app.models.boutique import Boutique


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# INSCRIPTION - PAGE
# =====================================================

@router.get("/register")
async def register_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


# =====================================================
# INSCRIPTION - TRAITEMENT
# =====================================================

@router.post("/register")
async def register_user(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # Vérifier si le numéro existe déjà
        # -------------------------------------------------

        existing_user = (
            db.query(User)
            .filter(User.phone == phone)
            .first()
        )

        if existing_user:

            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={
                    "error": "Ce numéro est déjà utilisé."
                }
            )

        # -------------------------------------------------
        # Créer l'utilisateur
        # -------------------------------------------------

        user = User(
            full_name=full_name,
            phone=phone,
            password=password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # -------------------------------------------------
        # Créer la session
        # -------------------------------------------------

        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name

        # Un nouvel utilisateur n'a pas encore de boutique
        request.session["has_boutique"] = False

        print("================================")
        print("INSCRIPTION RÉUSSIE")
        print("USER ID :", user.id)
        print("USER NAME :", user.full_name)
        print("HAS BOUTIQUE :", False)
        print("================================")

        return RedirectResponse(
            "/",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# CONNEXION - PAGE
# =====================================================

@router.get("/login")
async def login_page(request: Request):

    # Si déjà connecté
    if request.session.get("user_id"):

        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html"
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

    try:

        # -------------------------------------------------
        # Rechercher l'utilisateur
        # -------------------------------------------------

        user = (
            db.query(User)
            .filter(User.phone == phone)
            .first()
        )

        print("================================")
        print("PHONE REÇU :", repr(phone))
        print("PASSWORD REÇU :", repr(password))

        if user:

            print("USER TROUVÉ :", user.id)
            print("PHONE DB :", repr(user.phone))
            print("PASSWORD DB :", repr(user.password))

        else:

            print("USER NON TROUVÉ")

        # -------------------------------------------------
        # Vérifier utilisateur + mot de passe
        # -------------------------------------------------

        if not user or user.password != password:

            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "error": "Numéro ou mot de passe incorrect."
                }
            )

        # -------------------------------------------------
        # Créer la session
        # -------------------------------------------------

        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name

        # -------------------------------------------------
        # Vérifier si l'utilisateur possède une boutique
        # -------------------------------------------------

        boutique = (
            db.query(Boutique)
            .filter(Boutique.user_id == user.id)
            .first()
        )

        request.session["has_boutique"] = boutique is not None

        # -------------------------------------------------
        # Affichage debug
        # -------------------------------------------------

        print("SESSION CRÉÉE")
        print("USER ID :", request.session.get("user_id"))
        print("USER NAME :", request.session.get("user_name"))
        print("HAS BOUTIQUE :", request.session.get("has_boutique"))
        print("================================")

        return RedirectResponse(
            "/",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# DÉCONNEXION
# =====================================================

@router.get("/logout")
async def logout(request: Request):

    # Supprimer complètement la session
    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=303
    )