from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.contact_message import ContactMessage


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# PAGE CONTACT
# =====================================================

@router.get("/contact")
async def page_contact(
    request: Request
):

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    message = request.session.pop(
        "message",
        None
    )

    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={
            "lang": lang,
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

        request.session["message"] = (
            "✅ Votre message a été envoyé "
            "avec succès. Merci de nous avoir contactés !"
        )


        return RedirectResponse(
            "/contact?lang=fr",
            status_code=303
        )


    except Exception as e:

        db.rollback()


        # IMPORTANT :
        # afficher la vraie erreur dans le terminal

        print("")
        print("======================================")
        print("❌ ERREUR CONTACT")
        print(type(e).__name__)
        print(str(e))
        print("======================================")
        print("")


        request.session["message"] = (
            "❌ Impossible d'envoyer le message. "
            "Vérifiez le serveur."
        )


        return RedirectResponse(
            "/contact?lang=fr",
            status_code=303
        )


    finally:

        db.close()