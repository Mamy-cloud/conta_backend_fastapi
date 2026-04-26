# ================================================
# table_detail_info_collected.py
# JOIN collect_info_from_temoin → info_perso_temoin
# via temoin_id (premier élément du JSON questionnaire)
# ================================================

from sqlalchemy import text
from app.connexion_db.connexion_db import engine


def get_table_detail(user_id: str, query: str = "", region: str = "", statut: str = "") -> list[dict]:

    conditions = ["c.user_id = :user_id"]
    params: dict = {"user_id": user_id}

    if statut == "transcrit":
        conditions.append("c.traitement_transcription = 1")
    elif statut == "non-transcrit":
        conditions.append("c.traitement_transcription = 0")

    if region and region != "Toutes":
        conditions.append("i.region = :region")
        params["region"] = region

    if query:
        conditions.append("""
            (i.nom    ILIKE :query
          OR i.prenom ILIKE :query
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
            i.region
        FROM collect_info_from_temoin c
        LEFT JOIN info_perso_temoin i
            ON i.id = (c.questionnaire::jsonb -> 0 ->> 'valeur')
        WHERE {where_clause}
        ORDER BY c.created_at DESC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    results = []
    for row in rows:

        # ── Durée ─────────────────────────────────
        duree_s   = int(row.duree_audio or 0)
        h         = duree_s // 3600
        m         = (duree_s % 3600) // 60
        s         = duree_s % 60
        duree_fmt = f"{h}h {m}min {s}s"

        # ── Statut ────────────────────────────────
        statut_val = "transcrit" if row.traitement_transcription else "non-transcrit"

        # ── Témoin ────────────────────────────────
        temoin = f"{row.prenom or ''} {row.nom or ''}".strip() or ""

        # ── Région — null si vide ─────────────────
        region_val = None
        if row.departement or row.region:
            parts = [p for p in [row.departement, row.region] if p]
            region_val = " / ".join(parts)

        # ── Date ──────────────────────────────────
        date = str(row.created_at)[:10] if row.created_at else ""

        results.append({
            "id":           row.id,
            "titre":        row.questionnaire or "",
            "description":  row.url_audio     or "",
            "region":       region_val,
            "duree":        duree_fmt,
            "date":         date,
            "statut":       statut_val,
            "temoin":       temoin,
            "nom_temoin":   row.nom    or "",
            "prenom_temoin": row.prenom or "",
        })

    return results
