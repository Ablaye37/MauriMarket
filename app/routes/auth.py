from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import re

from app.database.database import SessionLocal
from app.models.user import User

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =====================================================
# GESTION DE LA LANGUE
# =====================================================

def get_language(request: Request):

    lang = request.query_params.get("lang", "fr")

    if lang not in ["fr", "ar"]:
        lang = "fr"

    translations = FR if lang == "fr" else AR

    return lang, translations


# =====================================================
# INSCRIPTION - PAGE
# =====================================================

@router.get("/register")
async def register_page(request: Request):

    lang, translations = get_language(request)

    message = request.session.pop("message", None)

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "message": message,
            "lang": lang,
            "t": translations
        }
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

    lang, translations = get_language(request)

    db = SessionLocal()

    try:

        # =================================================
        # NETTOYER LES DONNÉES
        # =================================================

        full_name = full_name.strip()
        phone = phone.strip()

        # =================================================
        # VÉRIFIER LE NUMÉRO MOBILE MAURITANIEN
        # =================================================

        if not re.fullmatch(
            r"(20|21|22|23|24|26|27|28|29|30|31|32|33|34|36|37|38|39|40|41|42|43|44|46|47|48|49)[0-9]{6}",
            phone
        ):

            request.session["message"] = (
                translations["invalid_phone"]
            )

            return RedirectResponse(
                f"/register?lang={lang}",
                status_code=303
            )

        # =================================================
        # VÉRIFIER SI LE NUMÉRO EXISTE DÉJÀ
        # =================================================

        existing_user = db.query(User).filter(
            User.phone == phone
        ).first()

        if existing_user:

            request.session["message"] = (
                translations["account_exists"]
            )

            return RedirectResponse(
                f"/register?lang={lang}",
                status_code=303
            )

        # =================================================
        # CRÉATION DU COMPTE
        # =================================================

        user = User(
            full_name=full_name,
            phone=phone,
            password=password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # =================================================
        # CONNEXION AUTOMATIQUE
        # =================================================

        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name

        # =================================================
        # MESSAGE DE BIENVENUE
        # =================================================

        request.session["message"] = (
            translations["register_success"]
        )

        return RedirectResponse(
            f"/?lang={lang}",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print("================================")
        print("ERREUR INSCRIPTION :", repr(e))
        print("================================")

        request.session["message"] = (
            translations["server_error"]
        )

        return RedirectResponse(
            f"/register?lang={lang}",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# CONNEXION - PAGE
# =====================================================

@router.get("/login")
async def login_page(request: Request):

    lang, translations = get_language(request)

    message = request.session.pop("message", None)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "message": message,
            "lang": lang,
            "t": translations
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

    lang, translations = get_language(request)

    db = SessionLocal()

    try:

        # =================================================
        # NETTOYER LE NUMÉRO
        # =================================================

        phone = phone.strip()

        # =================================================
        # RECHERCHER L'UTILISATEUR
        # =================================================

        user = db.query(User).filter(
            User.phone == phone
        ).first()

        print("================================")
        print("PHONE REÇU :", repr(phone))
        print("PASSWORD REÇU :", repr(password))

        # =================================================
        # UTILISATEUR INTROUVABLE
        # =================================================

        if not user:

            request.session["message"] = (
                translations["invalid_credentials"]
            )

            return RedirectResponse(
                f"/login?lang={lang}",
                status_code=303
            )

        print("USER TROUVÉ :", user.id)
        print("PHONE DB :", repr(user.phone))
        print("PASSWORD DB :", repr(user.password))

        # =================================================
        # MOT DE PASSE INCORRECT
        # =================================================

        if user.password != password:

            request.session["message"] = (
                translations["invalid_credentials"]
            )

            return RedirectResponse(
                f"/login?lang={lang}",
                status_code=303
            )

        # =================================================
        # CONNEXION RÉUSSIE
        # =================================================

        print("CONNEXION RÉUSSIE")

        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name

        request.session["message"] = (
            translations["login_success"]
        )

        return RedirectResponse(
            f"/?lang={lang}",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print("================================")
        print("ERREUR CONNEXION :", repr(e))
        print("================================")

        request.session["message"] = (
            translations["server_error"]
        )

        return RedirectResponse(
            f"/login?lang={lang}",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# DÉCONNEXION
# =====================================================

@router.get("/logout")
async def logout(request: Request):

    lang, translations = get_language(request)

    request.session.clear()

    request.session["message"] = (
        translations["logout_success"]
    )

    return RedirectResponse(
        f"/?lang={lang}",
        status_code=303
    )