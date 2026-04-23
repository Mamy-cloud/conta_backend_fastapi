import json
import logging
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.connexion_cloud.connexion_db import get_db

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


# ─────────────────────────────────────────────────────────────
# SAFE ENGINE ACCESS (évite crash au import)
# ─────────────────────────────────────────────────────────────

def _get_engine():
    from app.connexion_cloud.connexion_db import engine
    return engine


# ─────────────────────────────────────────────────────────────
# TABLE CHECK (SAFE)
# ─────────────────────────────────────────────────────────────

def _check_tables_and_relations() -> dict:
    engine = _get_engine()

    inspector = inspect(engine)
    existing = inspector.get_table_names()

    logger.debug(f"Tables existantes : {existing}")

    required = {
        "login_user",
        "info_perso_temoin",
        "collect_info_from_temoin",
        "info_perso_temoin_collect",
    }

    missing = required - set(existing)

    if missing:
        logger.warning(f"Tables manquantes → création : {missing}")
        try:
            create_all_tables()
        except Exception as e:
            logger.error(f"Erreur création tables : {e}", exc_info=True)
            raise

    fk_status = {}

    for table in required:
        try:
            fks = inspector.get_foreign_keys(table)
        except Exception:
            fks = []

        fk_status[table] = [
            {
                "colonne": fk.get("constrained_columns"),
                "référence_table": fk.get("referred_table"),
                "référence_colonne": fk.get("referred_columns"),
            }
            for fk in fks
        ]

    return {
        "tables_existantes": list(existing),
        "tables_manquantes": list(missing),
        "tables_créées": list(missing) if missing else [],
        "foreign_keys": fk_status,
    }


# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────

@router.get(
    "/health",
    summary="Vérifie DB + serveur",
    status_code=status.HTTP_200_OK,
)
def check_db_health():
    try:
        result = _check_tables_and_relations()

        return {
            "success": True,
            "status": "ok",
            "message": "Serveur opérationnel",
            "details": result,
        }

    except Exception as e:
        logger.error(f"Health check error : {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e)},
        )


# ─────────────────────────────────────────────────────────────
# SYNC MOBILE
# ─────────────────────────────────────────────────────────────

@router.post(
    "/sync",
    summary="Sync mobile → cloud",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
)
async def sync_from_mobile(
    user_id: str = Form(...),
    temoin: str = Form(...),
    questionnaire: str = Form(...),
    duree_audio: int = Form(0),
    audio: UploadFile = File(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    logger.info(f"sync_from_mobile user_id={user_id}")

    # ── CHECK TABLES SAFE ──
    try:
        _check_tables_and_relations()
    except Exception as e:
        logger.error(f"Table error : {e}", exc_info=True)
        return SyncResponse(
            success=False,
            message=f"Erreur DB init : {str(e)}",
        )

    # ── VALID JSON ──
    try:
        json.loads(temoin)
        json.loads(questionnaire)
    except Exception as e:
        return SyncResponse(
            success=False,
            message=f"JSON invalide : {str(e)}",
        )

    # ── SYNC LOGIC ──
    try:
        response = await handle_sync_from_mobile(
            db=db,
            user_id=user_id,
            temoin_json=temoin,
            questionnaire_json=questionnaire,
            audio_file=audio,
            image_file=image,
            duree_audio=duree_audio,
        )

        return response

    except Exception as e:
        logger.error(f"sync error : {e}", exc_info=True)
        return SyncResponse(
            success=False,
            message=str(e),
        )


# ─────────────────────────────────────────────────────────────
# GET COLLECTES
# ─────────────────────────────────────────────────────────────

@router.get(
    "/collectes/{user_id}",
    summary="Collectes utilisateur",
)
def get_collectes_by_user(user_id: str, db: Session = Depends(get_db)):
    try:
        user = db.query(LoginUser).filter(LoginUser.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": "Utilisateur introuvable"},
            )

        collectes = db.query(CollectInfoFromTemoin).filter(
            CollectInfoFromTemoin.user_id == user_id
        ).all()

        return {
            "success": True,
            "user_id": user_id,
            "total": len(collectes),
            "collectes": [
                {
                    "id": c.id,
                    "url_audio": c.url_audio,
                    "duree_audio": c.duree_audio,
                    "synced": c.synced,
                    "created_at": c.created_at,
                }
                for c in collectes
            ],
        }

    except Exception as e:
        logger.error(f"get_collectes error : {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e)},
        )