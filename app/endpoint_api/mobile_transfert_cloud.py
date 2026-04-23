import json
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.connexion_db.connexion_db import get_db
from app.models.base_model_from_mobile import SyncResponse
from app.request_command.transfert_cloud_from_mobile import handle_sync_from_mobile
from app.request_command.request_create_table import (
    Base,
    LoginUser,
    InfoPersoTemoin,
    CollectInfoFromTemoin,
    InfoPersoTemoinCollect,
    create_all_tables,
)
from app.connexion_db.connexion_db import engine

router = APIRouter(
    prefix="/mobile/transfert/cloud",
    tags=["Mobile — Transfert Cloud"],
)


# ─── Helper : vérifie que toutes les tables et relations existent ─────────────

def _check_tables_and_relations() -> dict:
    """
    Vérifie que les 4 tables existent en base et que les foreign keys
    sont bien en place. Crée les tables manquantes si nécessaire.
    """
    inspector = inspect(engine)
    existing  = inspector.get_table_names()

    required = {
        "login_user",
        "info_perso_temoin",
        "collect_info_from_temoin",
        "info_perso_temoin_collect",
    }

    missing = required - set(existing)

    # Crée les tables manquantes automatiquement
    if missing:
        create_all_tables()

    # Vérifie les foreign keys après création éventuelle
    fk_status = {}
    for table in required:
        fks = inspector.get_foreign_keys(table)
        fk_status[table] = [
            {
                "colonne":          fk["constrained_columns"],
                "référence_table":  fk["referred_table"],
                "référence_colonne":fk["referred_columns"],
            }
            for fk in fks
        ]

    return {
        "tables_existantes":  list(existing),
        "tables_manquantes":  list(missing),
        "tables_créées":      list(missing) if missing else [],
        "foreign_keys":       fk_status,
    }


# ─── GET /mobile/transfert/cloud/health ───────────────────────────────────────

@router.get(
    "/health",
    summary="Vérifie les tables et relations PostgreSQL",
    status_code=status.HTTP_200_OK,
)
def check_db_health():
    """
    Vérifie que toutes les tables et foreign keys sont en place.
    Crée les tables manquantes si nécessaire.
    """
    try:
        result = _check_tables_and_relations()
        return {
            "status":  "ok",
            "details": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur vérification DB : {str(e)}",
        )


# ─── POST /mobile/transfert/cloud/sync ────────────────────────────────────────

@router.post(
    "/sync",
    summary="Reçoit une collecte depuis le mobile et synchronise vers le cloud",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
)
async def sync_from_mobile(
    user_id:            str        = Form(...,  description="ID de l'utilisateur mobile"),
    temoin:             str        = Form(...,  description="JSON stringifié du témoin"),
    questionnaire:      str        = Form(...,  description="JSON stringifié du questionnaire"),
    duree_audio:        int        = Form(0,    description="Durée de l'audio en secondes"),
    audio:              UploadFile = File(None, description="Fichier audio (optionnel)"),
    image:              UploadFile = File(None, description="Photo du témoin (optionnel)"),
    db:                 Session    = Depends(get_db),
):
    """
    Endpoint principal appelé par le mobile (multipart/form-data).

    Flux :
    1. Vérifie les tables et relations PostgreSQL
    2. Parse le JSON temoin + questionnaire
    3. Upload audio → bucket Supabase collect_audio
    4. Upload image → bucket Supabase collect_audio
    5. Upsert témoin → table info_perso_temoin
    6. Crée collecte → table collect_info_from_temoin (synced = 1)
    7. Crée lien     → table info_perso_temoin_collect
    8. Commit et retourne SyncResponse
    """

    # 1. Vérifie / crée les tables ────────────────────────────────────────────
    try:
        _check_tables_and_relations()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur initialisation tables : {str(e)}",
        )

    # 2. Validation JSON basique ──────────────────────────────────────────────
    try:
        json.loads(temoin)
        json.loads(questionnaire)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"JSON invalide : {str(e)}",
        )

    # 3. Traitement principal ─────────────────────────────────────────────────
    response = await handle_sync_from_mobile(
        db                 = db,
        user_id            = user_id,
        temoin_json        = temoin,
        questionnaire_json = questionnaire,
        audio_file         = audio,
        image_file         = image,
        duree_audio        = duree_audio,
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message,
        )

    return response


# ─── GET /mobile/transfert/cloud/collectes/{user_id} ─────────────────────────

@router.get(
    "/collectes/{user_id}",
    summary="Récupère toutes les collectes synchronisées d'un utilisateur",
    status_code=status.HTTP_200_OK,
)
def get_collectes_by_user(
    user_id: str,
    db:      Session = Depends(get_db),
):
    """Retourne toutes les collectes d'un utilisateur (synced = 1)."""
    user = db.query(LoginUser).filter(LoginUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur '{user_id}' introuvable",
        )

    collectes = (
        db.query(CollectInfoFromTemoin)
        .filter(CollectInfoFromTemoin.user_id == user_id)
        .all()
    )

    return {
        "user_id":   user_id,
        "total":     len(collectes),
        "collectes": [
            {
                "id":           c.id,
                "url_audio":    c.url_audio,
                "duree_audio":  c.duree_audio,
                "synced":       c.synced,
                "created_at":   c.created_at,
            }
            for c in collectes
        ],
    }
