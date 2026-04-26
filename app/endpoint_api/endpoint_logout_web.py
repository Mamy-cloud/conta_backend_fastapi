# ================================================
# endpoint_logout_web.py
# Endpoint POST /logout/web/conta
# Supprime les 3 cookies HttpOnly de session
# ================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

COOKIE_DEL_OPTS = dict(
    httponly = True,
    secure   = False,    # False en dev local (HTTP)
    samesite = "lax",
)


@router.post(
    "/logout/web/conta",
    summary="Déconnexion d'un utilisateur web",
    tags=["Auth"],
)
async def logout_web() -> JSONResponse:
    """
    Supprime les cookies HttpOnly :
      - session_user_id
      - session_identifiant
      - session_email
    Le navigateur les efface dès réception de la réponse.
    """

    response = JSONResponse(
        content={
            "success": True,
            "message": "Déconnexion réussie.",
        }
    )

    response.delete_cookie(key="session_user_id",     **COOKIE_DEL_OPTS)
    response.delete_cookie(key="session_identifiant", **COOKIE_DEL_OPTS)
    response.delete_cookie(key="session_email",       **COOKIE_DEL_OPTS)

    return response
