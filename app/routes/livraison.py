from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# PAGE LIVRAISON
# =====================================================

@router.get("/livraison")
async def page_livraison(
    request: Request
):

    # -------------------------------------------------
    # LANGUE
    # -------------------------------------------------

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    if lang not in ["fr", "ar"]:
        lang = "fr"


    # -------------------------------------------------
    # TRADUCTIONS
    # -------------------------------------------------

    translations = (
        FR
        if lang == "fr"
        else AR
    )


    # -------------------------------------------------
    # AFFICHER LA PAGE
    # -------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="livraison.html",
        context={

            # Langue
            "lang": lang,

            # Traductions
            "t": translations

        }
    )