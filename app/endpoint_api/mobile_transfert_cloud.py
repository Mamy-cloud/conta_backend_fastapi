import json
import logging
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.connexion_db.connexion_db import get_db, engine
from app.models.base_model_from_mobile import SyncResponse
from app.request_command.transfert_cloud_from_mobile import handle_sync_from_mobile
from app.request_command.request_create_table import (
    LoginUser,
    CollectInfoFromTemoin,
    create_all_tables,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mobile/transfert/cloud",
    tags=["Mobile — Transfert Cloud"],
)


# ─── Helper : vérifie que toutes les tables existent ─────────────────────────

def _check_tables_and_relations() -> dict:
    inspector = inspect(engine)
    existing  = inspector.get_table_names()
    logger.debug(f"Tables existantes : {existing}")

    required = {
        "login_user",
        "info_perso_temoin",
        "collect_info_from_temoin",
        "info_perso_temoin_collect",
    }
    missing = required - set(existing)
    if missing:
        logger.warning(f"Tables manquantes, création : {missing}")
        create_all_tables()

    fk_status = {}
    for table in required:
        fks = inspector.get_foreign_keys(table)
        fk_status[table] = [
            {
                "colonne":           fk["constrained_columns"],
                "référence_table":   fk["referred_table"],
                "référence_colonne": fk["referred_columns"],
            }
            for fk in fks
        ]
    return {
        "tables_existantes": list(existing),
        "tables_manquantes": list(missing),
        "tables_créées":     list(missing) if missing else [],
        "foreign_keys":      fk_status,
    }


# ─── GET /health ──────────────────────────────────────────────────────────────

@router.get(
    "/health",
    summary="Vérifie les tables et confirme que le serveur est opérationnel",
    status_code=status.HTTP_200_OK,
)
def check_db_health():
    """
    Appelé par le mobile avant chaque synchronisation.
    Retourne success=True si le serveur et la DB sont prêts.
    """
    try:
        result = _check_tables_and_relations()
        logger.info("Health check OK")
        return {
            "success": True,
            "status":  "ok",
            "message": "Serveur opérationnel",
            "details": result,
        }
    except Exception as e:
        logger.error(f"Erreur health check : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Erreur serveur : {str(e)}",
            },
        )


# ─── POST /sync ───────────────────────────────────────────────────────────────

@router.post(
    "/sync",
    summary="Reçoit une collecte depuis le mobile et synchronise vers le cloud",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
)
async def sync_from_mobile(
    user_id:       str        = Form(...),
    temoin:        str        = Form(...),
    questionnaire: str        = Form(...),
    duree_audio:   int        = Form(0),
    audio:         UploadFile = File(None),
    image:         UploadFile = File(None),
    db:            Session    = Depends(get_db),
):
    """
    Endpoint principal appelé par le mobile (multipart/form-data).
    Retourne toujours un SyncResponse avec success=True ou False.
    """
    logger.info(f"sync_from_mobile — user_id={user_id}")
    logger.debug(f"audio={audio.filename if audio else None} | image={image.filename if image else None}")

    # 1. Vérifie les tables
    try:
        _check_tables_and_relations()
    except Exception as e:
        logger.error(f"Erreur tables : {e}", exc_info=True)
        return SyncResponse(
            success = False,
            message = f"Erreur initialisation tables : {str(e)}",
        )

    # 2. Valide le JSON
    try:
        json.loads(temoin)
        json.loads(questionnaire)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide : {e}")
        return SyncResponse(
            success = False,
            message = f"JSON invalide : {str(e)}",
        )

    # 3. Traitement principal
    response = await handle_sync_from_mobile(
        db                 = db,
        user_id            = user_id,
        temoin_json        = temoin,
        questionnaire_json = questionnaire,
        audio_file         = audio,
        image_file         = image,
        duree_audio        = duree_audio,
    )

    if response.success:
        logger.info(f"Sync OK — collect_id={response.collect_id}")
    else:
        logger.error(f"Sync échoué : {response.message}")

    # Retourne toujours 200 avec success=True/False
    # (le mobile lit le champ success pour décider)
    return response


# ─── GET /collectes/{user_id} ─────────────────────────────────────────────────

@router.get(
    "/collectes/{user_id}",
    summary="Collectes synchronisées d'un utilisateur",
    status_code=status.HTTP_200_OK,
)
def get_collectes_by_user(user_id: str, db: Session = Depends(get_db)):
    logger.info(f"get_collectes — user_id={user_id}")
    try:
        user = db.query(LoginUser).filter(LoginUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": f"Utilisateur '{user_id}' introuvable"},
            )

        collectes = db.query(CollectInfoFromTemoin).filter(
            CollectInfoFromTemoin.user_id == user_id
        ).all()

        return {
            "success":   True,
            "user_id":   user_id,
            "total":     len(collectes),
            "collectes": [
                {
                    "id":          c.id,
                    "url_audio":   c.url_audio,
                    "duree_audio": c.duree_audio,
                    "synced":      c.synced,
                    "created_at":  c.created_at,
                }
                for c in collectes
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_collectes : {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e)},
        )
