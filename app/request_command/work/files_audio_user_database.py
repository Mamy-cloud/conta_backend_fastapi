# ================================================
# files_audio_user_database.py
# Statistiques audio pour l'interface de travail
# ================================================

from sqlalchemy import text
from app.connexion_db.connexion_db import engine


def get_stats_audio(user_id: str) -> dict:
    """
    Retourne les statistiques audio pour un utilisateur :
    - total_heures     : durée totale formatée (Xh Ymin Zs)
    - total_fichiers   : nombre de lignes dans collect_info_from_temoin
    - total_transcrits : nombre de traitement_transcription = 1
    - total_non_transcrits : nombre de traitement_transcription = 0
    - progression_pct  : pourcentage vers 200h (TTS qualité)
    """

    with engine.connect() as conn:

        # ── Durée totale ──────────────────────────────
        row_duree = conn.execute(text("""
            SELECT COALESCE(SUM(duree_audio), 0) AS total_secondes
            FROM collect_info_from_temoin
            WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchone()

        total_secondes = int(row_duree.total_secondes) if row_duree else 0

        heures  = total_secondes // 3600
        minutes = (total_secondes % 3600) // 60
        secondes = total_secondes % 60
        total_heures_formate = f"{heures}h {minutes}min {secondes}s"
        total_heures_decimal = round(total_secondes / 3600, 2)

        # ── Total fichiers ────────────────────────────
        row_total = conn.execute(text("""
            SELECT COUNT(*) AS total
            FROM collect_info_from_temoin
            WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchone()

        total_fichiers = int(row_total.total) if row_total else 0

        # ── Transcrits ────────────────────────────────
        row_transcrits = conn.execute(text("""
            SELECT COUNT(*) AS total
            FROM collect_info_from_temoin
            WHERE user_id = :user_id
              AND traitement_transcription = 1
        """), {"user_id": user_id}).fetchone()

        total_transcrits = int(row_transcrits.total) if row_transcrits else 0

        # ── Non transcrits ────────────────────────────
        row_non_transcrits = conn.execute(text("""
            SELECT COUNT(*) AS total
            FROM collect_info_from_temoin
            WHERE user_id = :user_id
              AND traitement_transcription = 0
        """), {"user_id": user_id}).fetchone()

        total_non_transcrits = int(row_non_transcrits.total) if row_non_transcrits else 0

        # ── Progression TTS ───────────────────────────
        TTS_SEUIL_BASE    = 50
        TTS_SEUIL_QUALITE = 200
        progression_pct   = round(min((total_heures_decimal / TTS_SEUIL_QUALITE) * 100, 100), 2)

    return {
        "total_heures":           total_heures_formate,
        "total_heures_decimal":   total_heures_decimal,
        "total_fichiers":         total_fichiers,
        "total_transcrits":       total_transcrits,
        "total_non_transcrits":   total_non_transcrits,
        "progression_pct":        progression_pct,
        "tts_seuil_base":         TTS_SEUIL_BASE,
        "tts_seuil_qualite":      TTS_SEUIL_QUALITE,
    }
