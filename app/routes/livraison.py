from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


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

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    return templates.TemplateResponse(
        request=request,
        name="livraison.html",
        context={
            "lang": lang
        }
    )   