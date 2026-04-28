# ================================================
# endpoint_list_of_data_collected.py
# Endpoint GET /list/data/collected
# Retourne toutes les données collectées
# avec info_perso_temoin + login_user
# ================================================

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.connexion_db.connexion_db import engine

router = APIRouter()


@router.get(
    "/list/data/collected",
    summary="Liste de toutes les données collectées",
    tags=["Admin"],
)
async def get_all_data_collected(
    request: Request,
    query:   str = Query(default="",       description="Recherche libre"),
    region:  str = Query(default="Toutes", description="Filtre région"),
    statut:  str = Query(default="",       description="transcrit | non-transcrit"),
) -> JSONResponse:

    role = request.cookies.get("session_role", "user")
    if role != "admin":
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Accès refusé."},
        )

    conditions = ["1=1"]
    params: dict = {}

    if statut == "transcrit":
        conditions.append("c.traitement_transcription = 1")
    elif statut == "non-transcrit":
        conditions.append("c.traitement_transcription = 0")

    if region and region != "Toutes":
        conditions.append("i.region = :region")
        params["region"] = region

    if query:
        conditions.append("""
            (i.nom          ILIKE :query
          OR i.prenom       ILIKE :query
          OR lu.identifiant ILIKE :query
          OR c.questionnaire ILIKE :query)
        """)
        params["query"] = f"%{query}%"

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            c.id,
            c.questionnaire,
            c.url_audio,
            c.duree_audio,
            c.traitement_transcription,
            c.created_at,
            i.nom,
            i.prenom,
            i.departement,
            i.region,
            lu.identifiant         AS interviewer_identifiant
        FROM collect_info_from_temoin c
        LEFT JOIN info_perso_temoin i
            ON i.id = (c.questionnaire::jsonb -> 0 ->> 'valeur')
        LEFT JOIN login_user lu ON lu.id = c.user_id
        WHERE {where_clause}
        ORDER BY c.created_at DESC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    results = []
    for row in rows:
        duree_s   = int(row.duree_audio or 0)
        h         = duree_s // 3600
        m         = (duree_s % 3600) // 60
        s         = duree_s % 60
        duree_fmt = f"{h}h {m}min {s}s"

        statut_val = "transcrit" if row.traitement_transcription else "non-transcrit"

        temoin = f"{row.prenom or ''} {row.nom or ''}".strip() or "—"

        region_val = None
        if row.departement or row.region:
            parts = [p for p in [row.departement, row.region] if p]
            region_val = " / ".join(parts)

        date = str(row.created_at)[:10] if row.created_at else "—"

        results.append({
            "id":           row.id,
            "titre":        row.questionnaire or "",
            "url_audio":    row.url_audio     or "",
            "description":  row.url_audio     or "",
            "region":       region_val,
            "duree":        duree_fmt,
            "date":         date,
            "statut":       statut_val,
            "temoin":       temoin,
            "nom_temoin":   row.nom    or "",
            "prenom_temoin": row.prenom or "",
            "interviewer":  row.interviewer_identifiant or "—",
        })

    return JSONResponse(
        status_code=200,
        content={"success": True, "tableau": results},
    )
