import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.connexion_cloud.connexion_bucket import upload_audio, upload_image
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


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _now() -> str:
    return datetime.utcnow().isoformat()


def _safe_uuid(value: Optional[str]) -> str:
    return value if value else str(uuid.uuid4())


# ─────────────────────────────────────────────
# TEMOIN UPSERT SAFE
# ─────────────────────────────────────────────

def _upsert_temoin(db: Session, temoin_data: TemoinFromMobile, image_url: str | None):
    temoin_id = _safe_uuid(temoin_data.id)

    temoin = db.query(InfoPersoTemoin).filter_by(id=temoin_id).first()

    if not temoin:
        temoin = InfoPersoTemoin(
            id=temoin_id,
            user_id=temoin_data.user_id,
            nom=temoin_data.nom or "",
            prenom=temoin_data.prenom or "",
            date_naissance=temoin_data.date_naissance,
            departement=temoin_data.departement,
            region=temoin_data.region,

            # 🔥 SAFE JSON STORAGE
            contacts=json.dumps(temoin_data.contacts or [], ensure_ascii=False),

            signature_url=temoin_data.signature_url,
            accepte_rgpd=temoin_data.accepte_rgpd or 0,
            date_creation=temoin_data.date_creation or _now(),

            img_temoin=image_url or temoin_data.img_temoin,
        )
        db.add(temoin)

    else:
        if temoin_data.nom:
            temoin.nom = temoin_data.nom
        if temoin_data.prenom:
            temoin.prenom = temoin_data.prenom
        if temoin_data.date_naissance:
            temoin.date_naissance = temoin_data.date_naissance
        if temoin_data.departement:
            temoin.departement = temoin_data.departement
        if temoin_data.region:
            temoin.region = temoin_data.region
        if temoin_data.contacts is not None:
            temoin.contacts = json.dumps(temoin_data.contacts, ensure_ascii=False)
        if image_url:
            temoin.img_temoin = image_url

    db.flush()
    return temoin


# ─────────────────────────────────────────────
# COLLECT UPSERT
# ─────────────────────────────────────────────

def _upsert_collecte(
    db: Session,
    user_id: str,
    questionnaire: list[QuestionnaireItem],
    audio_url: Optional[str],
    duree_audio: int,
):
    collecte_id = str(uuid.uuid4())

    collecte = CollectInfoFromTemoin(
        id=collecte_id,
        user_id=user_id,

        questionnaire=json.dumps(
            [item.model_dump() for item in questionnaire],
            ensure_ascii=False,
        ),

        url_audio=audio_url,
        duree_audio=duree_audio,
        synced=1,
        created_at=_now(),
    )

    db.add(collecte)
    db.flush()

    return collecte


# ─────────────────────────────────────────────
# LINK TABLE
# ─────────────────────────────────────────────

def _create_link(db: Session, collecte_id: str):
    db.add(
        InfoPersoTemoinCollect(
            id=str(uuid.uuid4()),
            collect_id=collecte_id,
            created_at=_now(),
        )
    )
    db.flush()


# ─────────────────────────────────────────────
# MAIN SYNC FUNCTION
# ─────────────────────────────────────────────

async def handle_sync_from_mobile(
    db: Session,
    user_id: str,
    temoin_json: str,
    questionnaire_json: str,
    audio_file: UploadFile | None = None,
    image_file: UploadFile | None = None,
    duree_audio: int = 0,
) -> SyncResponse:

    try:
        logger.info(f"sync start user_id={user_id}")

        # ───────────── JSON PARSING SAFE ─────────────
        temoin_data = TemoinFromMobile.model_validate_json(temoin_json)

        try:
            questionnaire_raw = json.loads(questionnaire_json)
        except Exception:
            questionnaire_raw = []

        questionnaire = [
            QuestionnaireItem(**item) for item in questionnaire_raw
            if isinstance(item, dict)
        ]

        # ───────────── AUDIO UPLOAD SAFE ─────────────
        audio_url = None
        if audio_file and getattr(audio_file, "filename", None):
            audio_bytes = await audio_file.read()
            audio_url = upload_audio(
                audio_bytes,
                f"audio/{user_id}/{uuid.uuid4()}_{audio_file.filename}"
            )

        # ───────────── IMAGE UPLOAD SAFE ─────────────
        image_url = None
        if image_file and getattr(image_file, "filename", None):
            image_bytes = await image_file.read()
            image_url = upload_image(
                image_bytes,
                f"image/{user_id}/{uuid.uuid4()}_{image_file.filename}"
            )

        # ───────────── DB OPERATIONS ─────────────
        temoin = _upsert_temoin(db, temoin_data, image_url)
        collecte = _upsert_collecte(
            db, user_id, questionnaire, audio_url, duree_audio
        )
        _create_link(db, collecte.id)

        db.commit()

        return SyncResponse(
            success=True,
            collect_id=collecte.id,
            audio_url=audio_url,
            image_url=image_url,
            message="Sync OK",
        )

    except Exception as e:
        logger.error(f"sync error: {e}", exc_info=True)
        db.rollback()

        return SyncResponse(
            success=False,
            message=str(e),
        )