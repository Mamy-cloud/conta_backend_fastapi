# ================================================
# research_info_collected.py
# Recherche pour la barre de recherche
# de l'interface de travail
# ================================================

from sqlalchemy import text
from app.connexion_db.connexion_db import engine


def search_collected_info(user_id: str, query: str = "", region: str = "", statut: str = "") -> list[dict]:
    """
    Recherche dans collect_info_from_temoin directement
    via les colonnes nom_temoin, prenom_temoin, nom_region, nom_departement.
    """

    conditions = ["user_id = :user_id"]
    params: dict = {"user_id": user_id}

    if statut == "transcrit":
        conditions.append("traitement_transcription = 1")
    elif statut == "non-transcrit":
        conditions.append("traitement_transcription = 0")

    if region and region != "Toutes":
        conditions.append("nom_region = :region")
        params["region"] = region

    if query:
        conditions.append("""
            (nom_temoin    ILIKE :query
          OR prenom_temoin ILIKE :query
          OR questionnaire ILIKE :query)
        """)
        params["query"] = f"%{query}%"

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            id,
            questionnaire,
            url_audio,
            duree_audio,
            traitement_transcription,
            nom_departement,
            nom_region,
            nom_temoin,
            prenom_temoin,
            created_at
        FROM collect_info_from_temoin
        WHERE {where_clause}
        ORDER BY created_at DESC
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

        results.append({
            "id":                      row.id,
            "questionnaire":           row.questionnaire,
            "url_audio":               row.url_audio,
            "duree_audio":             duree_fmt,
            "traitement_transcription": bool(row.traitement_transcription),
            "created_at":              row.created_at,
            "nom_temoin":              row.nom_temoin    or "",
            "prenom_temoin":           row.prenom_temoin or "",
            "nom_region":              row.nom_region    or "",
            "nom_departement":         row.nom_departement or "",
        })

    return results
