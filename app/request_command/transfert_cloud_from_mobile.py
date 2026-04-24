import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.connexion_db.connexion_bucket import upload_audio, upload_image
from app.models.base_model_from_mobile import (
    TemoinFromMobile,
    QuestionnaireItem,
    SyncResponse,
)
from app.request_command.request_create_table import (
    InfoPersoTemoin,
    CollectInfoFromTemoin,
    InfoPersoTemoinCollect,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.utcnow().isoformat()


def _safe_uuid(value: Optional[str]) -> str:
    return value if value else str(uuid.uuid4())


def _upsert_temoin(db, temoin_data, image_url):
    temoin_id = _safe_uuid(temoin_data.id)
    logger.debug(f"_upsert_temoin — id={temoin_id}")

    temoin = db.query(InfoPersoTemoin).filter(InfoPersoTemoin.id == temoin_id).first()
    if temoin is None:
        logger.info(f"Création témoin : {temoin_id}")
        temoin = InfoPersoTemoin(
            id             = temoin_id,
            user_id        = temoin_data.user_id,
            nom            = temoin_data.nom            or "",
            prenom         = temoin_data.prenom         or "",
            date_naissance = temoin_data.date_naissance,
            departement    = temoin_data.departement,
            region         = temoin_data.region,
            img_temoin     = image_url or temoin_data.img_temoin,
            contacts       = temoin_data.contacts       or "[]",
            signature_url  = temoin_data.signature_url,
            accepte_rgpd   = temoin_data.accepte_rgpd   or 0,
            date_creation  = temoin_data.date_creation  or _now(),
        )
        db.add(temoin)
    else:
        logger.info(f"Mise à jour témoin : {temoin_id}")
        if temoin_data.nom:            temoin.nom            = temoin_data.nom
        if temoin_data.prenom:         temoin.prenom         = temoin_data.prenom
        if temoin_data.date_naissance: temoin.date_naissance = temoin_data.date_naissance
        if temoin_data.departement:    temoin.departement    = temoin_data.departement
        if temoin_data.region:         temoin.region         = temoin_data.region
        if temoin_data.contacts:       temoin.contacts       = temoin_data.contacts
        if temoin_data.signature_url:  temoin.signature_url  = temoin_data.signature_url
        if temoin_data.accepte_rgpd:   temoin.accepte_rgpd   = temoin_data.accepte_rgpd
        if image_url:                  temoin.img_temoin     = image_url

    db.flush()
    return temoin


def _create_collecte(db, user_id, questionnaire, audio_url, duree_audio, id_questionnaire):
    collecte_id = str(uuid.uuid4())
    logger.debug(f"_create_collecte — id={collecte_id} | id_questionnaire={id_questionnaire}")

    collecte = CollectInfoFromTemoin(
        id               = collecte_id,
        user_id          = user_id,
        questionnaire    = json.dumps(
            [item.model_dump() for item in questionnaire],
            ensure_ascii=False,
        ),
        url_audio        = audio_url,
        duree_audio      = duree_audio,
        synced           = 1,
        id_questionnaire = id_questionnaire,
        created_at       = _now(),
    )
    db.add(collecte)
    db.flush()
    return collecte


def _create_link(db, collecte_id):
    link = InfoPersoTemoinCollect(
        id         = str(uuid.uuid4()),
        collect_id = collecte_id,
        created_at = _now(),
    )
    db.add(link)
    db.flush()


async def handle_sync_from_mobile(
    db: Session,
    user_id: str,
    temoin_json: str,
    questionnaire_json: str,
    id_questionnaire: str,
    audio_file: Optional[UploadFile] = None,
    image_file: Optional[UploadFile] = None,
    duree_audio: int = 0,
) -> SyncResponse:
    try:
        logger.info(f"handle_sync_from_mobile — user_id={user_id} | id_questionnaire={id_questionnaire}")

        # 1. Parse JSON
        temoin_data   = TemoinFromMobile.model_validate_json(temoin_json)
        questionnaire = [QuestionnaireItem(**item) for item in json.loads(questionnaire_json)]

        # 2. Upload audio
        audio_url = None
        if audio_file and audio_file.filename:
            logger.info(f"Upload audio : {audio_file.filename}")
            audio_bytes    = await audio_file.read()
            audio_filename = f"audio/{user_id}/{uuid.uuid4()}_{audio_file.filename}"
            audio_url      = upload_audio(audio_bytes, audio_filename)
            logger.info(f"Audio uploadé : {audio_url}")

        # 3. Upload image
        image_url = None
        if image_file and image_file.filename:
            logger.info(f"Upload image : {image_file.filename}")
            image_bytes    = await image_file.read()
            image_filename = f"image/{user_id}/{uuid.uuid4()}_{image_file.filename}"
            image_url      = upload_image(image_bytes, image_filename)
            logger.info(f"Image uploadée : {image_url}")

        # 4. Upsert témoin
        temoin = _upsert_temoin(db, temoin_data, image_url)
        logger.info(f"Témoin upserted : {temoin.id}")

        # 5. Crée collecte avec id_questionnaire
        collecte = _create_collecte(
            db               = db,
            user_id          = user_id,
            questionnaire    = questionnaire,
            audio_url        = audio_url,
            duree_audio      = duree_audio,
            id_questionnaire = id_questionnaire,
        )
        logger.info(f"Collecte créée : {collecte.id}")

        # 6. Lien
        _create_link(db, collecte.id)

        # 7. Commit
        db.commit()
        logger.info("Commit OK ✅")

        return SyncResponse(
            success          = True,
            collect_id       = collecte.id,
            id_questionnaire = id_questionnaire,
            audio_url        = audio_url,
            image_url        = image_url,
            message          = "Synchronisation réussie",
        )

    except Exception as e:
        logger.error(f"Erreur handle_sync : {e}", exc_info=True)
        db.rollback()
        return SyncResponse(
            success = False,
            message = f"Erreur synchronisation : {str(e)}",
        )
