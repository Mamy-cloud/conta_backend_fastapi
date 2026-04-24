import json
import logging
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.connexion_db.connexion_db import get_db, engine
from app.models.base_model_from_mobile import (
    SyncResponse,
    CheckIdsRequest,
    CheckIdsResponse,
)
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


def _check_tables_and_relations() -> dict:
    inspector = inspect(engine)
    existing  = inspector.get_table_names()
    logger.debug(f"Tables existantes : {existing}")
    required  = {
        "login_user", "info_perso_temoin",
        "collect_info_from_temoin", "info_perso_temoin_collect",
    }
    missing = required - set(existing)
    if missing:
        logger.warning(f"Tables manquantes, création : {missing}")
        create_all_tables()
    return {"tables_existantes": list(existing), "tables_manquantes": list(missing)}


# ─── GET /health ──────────────────────────────────────────────────────────────

@router.get("/health", summary="Vérifie les tables et le serveur")
def check_db_health():
    try:
        result = _check_tables_and_relations()
        logger.info("Health check OK")
        return {"success": True, "status": "ok", "message": "Serveur opérationnel", "details": result}
    except Exception as e:
        logger.error(f"Erreur health : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "message": str(e)})


# ─── POST /check/ids ──────────────────────────────────────────────────────────
# Le mobile envoie tous ses id_questionnaire → FastAPI retourne ceux à transférer

@router.post(
    "/check/ids",
    response_model=CheckIdsResponse,
    summary="Vérifie quels id_questionnaire sont déjà en DB",
    status_code=status.HTTP_200_OK,
)
def check_ids(payload: CheckIdsRequest, db: Session = Depends(get_db)):
    """
    Reçoit la liste des id_questionnaire du mobile.
    Retourne :
      - ids_a_transferer : ceux qui n'existent PAS encore en DB → à envoyer
      - ids_deja_synced  : ceux qui existent déjà → à ignorer
    """
    logger.info(f"━━━ POST /check/ids — user_id={payload.user_id} | nb_ids={len(payload.id_questionnaires)}")
    logger.debug(f"IDs reçus : {payload.id_questionnaires}")

    if not payload.id_questionnaires:
        return CheckIdsResponse(
            ids_a_transferer   = [],
            ids_deja_synced    = [],
            total_envoye       = 0,
            total_a_transferer = 0,
        )

    # Cherche les ids déjà présents en DB
    existing = db.query(CollectInfoFromTemoin.id_questionnaire).filter(
        CollectInfoFromTemoin.id_questionnaire.in_(payload.id_questionnaires)
    ).all()

    ids_deja_synced  = [row[0] for row in existing]
    ids_a_transferer = [
        id for id in payload.id_questionnaires
        if id not in ids_deja_synced
    ]

    logger.info(f"✅ {len(ids_a_transferer)} à transférer | {len(ids_deja_synced)} déjà en DB")
    logger.debug(f"À transférer : {ids_a_transferer}")
    logger.debug(f"Déjà synced  : {ids_deja_synced}")

    return CheckIdsResponse(
        ids_a_transferer   = ids_a_transferer,
        ids_deja_synced    = ids_deja_synced,
        total_envoye       = len(payload.id_questionnaires),
        total_a_transferer = len(ids_a_transferer),
    )


# ─── POST /sync ───────────────────────────────────────────────────────────────

@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Reçoit une collecte et synchronise vers le cloud",
    status_code=status.HTTP_200_OK,
)
async def sync_from_mobile(
    user_id:          str        = Form(...),
    temoin:           str        = Form(...),
    questionnaire:    str        = Form(...),
    id_questionnaire: str        = Form(...),   # ← obligatoire pour anti-doublon
    duree_audio:      int        = Form(0),
    audio:            UploadFile = File(None),
    image:            UploadFile = File(None),
    db:               Session    = Depends(get_db),
):
    logger.info(f"━━━ POST /sync — user_id={user_id} | id_questionnaire={id_questionnaire}")

    # Vérifie les tables
    try:
        _check_tables_and_relations()
    except Exception as e:
        return SyncResponse(success=False, message=f"Erreur tables : {str(e)}")

    # Valide le JSON
    try:
        json.loads(temoin)
        json.loads(questionnaire)
    except json.JSONDecodeError as e:
        return SyncResponse(success=False, message=f"JSON invalide : {str(e)}")

    # Traitement principal
    response = await handle_sync_from_mobile(
        db                 = db,
        user_id            = user_id,
        temoin_json        = temoin,
        questionnaire_json = questionnaire,
        audio_file         = audio,
        image_file         = image,
        duree_audio        = duree_audio,
        id_questionnaire   = id_questionnaire,
    )

    if response.success:
        logger.info(f"✅ Sync OK — collect_id={response.collect_id}")
    else:
        logger.error(f"❌ Sync échoué : {response.message}")

    return response


# ─── GET /collectes/{user_id} ─────────────────────────────────────────────────

@router.get("/collectes/{user_id}", summary="Collectes d'un utilisateur")
def get_collectes_by_user(user_id: str, db: Session = Depends(get_db)):
    logger.info(f"get_collectes — user_id={user_id}")
    try:
        user = db.query(LoginUser).filter(LoginUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail={"success": False, "message": f"Utilisateur '{user_id}' introuvable"})

        collectes = db.query(CollectInfoFromTemoin).filter(
            CollectInfoFromTemoin.user_id == user_id
        ).all()

        return {
            "success":   True,
            "user_id":   user_id,
            "total":     len(collectes),
            "collectes": [
                {
                    "id":               c.id,
                    "id_questionnaire": c.id_questionnaire,
                    "url_audio":        c.url_audio,
                    "duree_audio":      c.duree_audio,
                    "synced":           c.synced,
                    "created_at":       c.created_at,
                }
                for c in collectes
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_collectes : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
