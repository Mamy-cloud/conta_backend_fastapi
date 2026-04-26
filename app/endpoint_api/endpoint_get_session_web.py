# ================================================
# endpoint_get_session_web.py
# Endpoint GET /session/web
# ================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get(
    "/session/web",
    summary="Récupère les infos de session depuis les cookies",
    tags=["Auth"],
)
async def get_session(request: Request) -> JSONResponse:

    user_id     = request.cookies.get("session_user_id")
    identifiant = request.cookies.get("session_identifiant")
    email       = request.cookies.get("session_email")
    nom         = request.cookies.get("session_nom")
    prenom      = request.cookies.get("session_prenom")

    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Non connecté."},
        )

    return JSONResponse(
        status_code=200,
        content={
            "success":     True,
            "user_id":     user_id,
            "identifiant": identifiant,
            "email":       email,
            "nom":         nom,
            "prenom":      prenom,
        },
    )
