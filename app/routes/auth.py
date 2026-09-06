from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import re

from app.database.database import SessionLocal
from app.models.user import User


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =====================================================
# INSCRIPTION
# =====================================================

@router.get("/register")
async def register_page(request: Request):

    message = request.session.pop("message", None)

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "message": message
        }
    )


@router.post("/register")
async def register_user(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    try:

        # =====================================================
        # NETTOYER LES DONNÉES
        # =====================================================

        full_name = full_name.strip()
        phone = phone.strip()

        # =====================================================
        # VÉRIFIER LE NUMÉRO MOBILE MAURITANIEN
        # =====================================================

        if not re.fullmatch(
            r"(20|21|22|23|24|26|27|28|29|30|31|32|33|34|36|37|38|39|40|41|42|43|44|46|47|48|49)[0-9]{6}",
            phone
        ):

            request.session["message"] = (
                "Veuillez entrer un numéro mobile mauritanien valide."
            )

            return RedirectResponse(
                "/register",
                status_code=303
            )

        # =====================================================
        # VÉRIFIER SI LE NUMÉRO EXISTE DÉJÀ
        # =====================================================

        existing_user = db.query(User).filter(
            User.phone == phone
        ).first()

        if existing_user:

            request.session["message"] = (
                "Ce compte existe déjà. Veuillez vous connecter."
            )

            return RedirectResponse(
                "/register",
                status_code=303
            )

        # =====================================================
        # CRÉATION DU NOUVEAU COMPTE
        # =====================================================

        user = User(
            full_name=full_name,
            phone=phone,
            password=password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # =====================================================
        # CONNEXION AUTOMATIQUE
        # =====================================================

        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name

        # =====================================================
        # MESSAGE DE BIENVENUE
        # =====================================================

        request.session["message"] = (
            "Votre compte a été créé avec succès. "
            "Bienvenue sur MauriMarket ! 🇲🇷"
        )

        return RedirectResponse(
            "/",
            status_code=303
        )

    except Exception as e:

        # Annuler toute modification éventuelle en base
        db.rollback()

        # Afficher l'erreur uniquement dans le terminal
        print("================================")
        print("ERREUR INSCRIPTION :", repr(e))
        print("================================")

        # Message simple pour l'utilisateur
        request.session["message"] = (
            "Une erreur est survenue lors de l'inscription. "
            "Veuillez réessayer."
        )

        return RedirectResponse(
            "/register",
            status_code=303
        )

    finally:

        db.close()


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

    if not user:
        db.close()

        request.session["message"] = (
            "Numéro de téléphone ou mot de passe incorrect."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )

    print("USER TROUVÉ :", user.id)
    print("PHONE DB :", repr(user.phone))
    print("PASSWORD DB :", repr(user.password))

    if user.password != password:
        db.close()

        request.session["message"] = (
            "Numéro de téléphone ou mot de passe incorrect."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )

    print("CONNEXION RÉUSSIE")

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name

    request.session["message"] = (
        "Connexion réussie. Bienvenue sur MauriMarket ! 🇲🇷"
    )

    db.close()

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
        "Vous avez été déconnecté avec succès ! 🇲🇷"
    )

    return RedirectResponse(
        "/",
        status_code=303
    )
