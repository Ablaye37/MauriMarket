
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.contact_message import ContactMessage

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# LANGUE
# =====================================================

def get_language(request: Request):
    lang = request.query_params.get("lang", "fr")

    if lang not in ("fr", "ar"):
        lang = "fr"

    translations = AR if lang == "ar" else FR

    return lang, translations


# =====================================================
# REDIRECTION AVEC LANGUE
# =====================================================

def redirect_with_lang(
    request: Request,
    url: str
):
    lang, _ = get_language(request)

    separator = "&" if "?" in url else "?"

    return RedirectResponse(
        f"{url}{separator}lang={lang}",
        status_code=303
    )


# =====================================================
# PAGE CONTACT
# =====================================================

@router.get("/contact")
async def page_contact(
    request: Request
):
    lang, translations = get_language(request)

    message = request.session.pop(
        "message",
        None
    )

    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={
            "lang": lang,
            "t": translations,
            "message": message
        }
    )


# =====================================================
# ENVOYER UN MESSAGE
# =====================================================

@router.post("/contact")
async def envoyer_message(
    request: Request,

    name: str = Form(...),

    phone: str = Form(...),

    email: str = Form(""),

    subject: str = Form(...),

    message: str = Form(...)
):
    lang, translations = get_language(request)

    db = SessionLocal()

    try:

        print("======================================")
        print("📩 NOUVEAU MESSAGE CONTACT")
        print("Nom :", name)
        print("Téléphone :", phone)
        print("Email :", email)
        print("Sujet :", subject)
        print("Message :", message)
        print("======================================")

        # =================================================
        # CRÉER LE MESSAGE
        # =================================================

        nouveau_message = ContactMessage(
            name=name.strip(),

            phone=phone.strip(),

            email=email.strip()
            if email
            else None,

            subject=subject.strip(),

            message=message.strip(),

            status="new"
        )

        # =================================================
        # AJOUTER À LA BASE
        # =================================================

        db.add(
            nouveau_message
        )

        db.commit()

        db.refresh(
            nouveau_message
        )

        print(
            "✅ MESSAGE CONTACT ENREGISTRÉ"
        )

        print(
            "ID :",
            nouveau_message.id
        )

        # =================================================
        # MESSAGE DE SUCCÈS
        # =================================================

        request.session["message"] = translations.get(
            "contact_success",
            translations.get(
                "success",
                "Votre message a été envoyé avec succès."
            )
        )

        return redirect_with_lang(
            request,
            "/contact"
        )

    except Exception as e:

        db.rollback()

        # =================================================
        # ERREUR
        # =================================================

        print("")
        print("======================================")
        print("❌ ERREUR CONTACT")
        print(type(e).__name__)
        print(str(e))
        print("======================================")
        print("")

        request.session["message"] = translations.get(
            "contact_error",
            translations.get(
                "error",
                "Impossible d'envoyer le message."
            )
        )

        return redirect_with_lang(
            request,
            "/contact"
        )

    finally:

        db.close()
