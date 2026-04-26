# ================================================
# endpoint_display_info_temoin.py
# Endpoint GET /info/temoin/conta
# Retourne toutes les données pour view_work.tsx
# ================================================

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from app.request_command.work.files_audio_user_database  import get_stats_audio
from app.request_command.work.table_detail_info_collected import get_table_detail

router = APIRouter()


@router.get(
    "/info/temoin/conta",
    summary="Données complètes pour l'interface de travail",
    tags=["Interface de travail"],
)
async def display_info_temoin(
    request: Request,
    query:   str = Query(default="",        description="Recherche libre"),
    region:  str = Query(default="Toutes",  description="Filtre région"),
    statut:  str = Query(default="",        description="transcrit | non-transcrit | ''"),
) -> JSONResponse:
    """
    Récupère l'user_id depuis le cookie HttpOnly session_user_id,
    puis retourne :
    - stats   : heures totales, fichiers, transcrits, non transcrits, progression TTS
    - tableau : liste des enregistrements avec témoin, région, durée, date, statut
    """

    user_id = request.cookies.get("session_user_id")

    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Non connecté."},
        )

    try:
        stats   = get_stats_audio(user_id)
        tableau = get_table_detail(user_id, query=query, region=region, statut=statut)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur serveur : {type(e).__name__} — {e}"},
        )

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "stats":   stats,
            "tableau": tableau,
        },
    )
