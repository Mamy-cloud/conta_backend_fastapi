# ================================================
# endpoint_list_of_interviewer_server.py
# Endpoint GET /admin/interviewers
# Retourne toutes les lignes de login_user
# ================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.connexion_db.connexion_db import engine

router = APIRouter()


@router.get(
    "/admin/interviewers",
    summary="Liste de tous les interviewers",
    tags=["Admin"],
)
async def get_all_interviewers(request: Request) -> JSONResponse:
    """
    Retourne toutes les lignes de la table login_user.
    Réservé à l'admin — vérifie le cookie session_role.
    """

    role = request.cookies.get("session_role", "user")
    if role != "admin":
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Accès refusé."},
        )

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                id,
                identifiant,
                nom,
                prenom,
                email,
                date_naissance,
                created_at
            FROM login_user
            ORDER BY created_at DESC
        """)).fetchall()

    interviewers = [
        {
            "id":             row.id,
            "identifiant":    row.identifiant,
            "nom":            row.nom            or "",
            "prenom":         row.prenom         or "",
            "email":          row.email          or "",
            "date_naissance": row.date_naissance or "",
            "created_at":     str(row.created_at)[:10] if row.created_at else "",
        }
        for row in rows
    ]

    return JSONResponse(
        status_code=200,
        content={"success": True, "interviewers": interviewers},
    )
