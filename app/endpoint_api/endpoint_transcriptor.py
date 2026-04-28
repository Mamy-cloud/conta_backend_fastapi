# ================================================
# endpoint_transcriptor.py
# Endpoints pour STT (Whisper) et TTS (MMS)
# ================================================

import os
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

from app.request_command.transcription.stt_whisper                       import transcribe_and_translate, transcribe_segments
from app.request_command.transcription.tts_mms                             import synthesize, synthesize_segments
from app.request_command.transcription.save_segmentation   import save_segments, load_segments, validate_segmentation, update_segment_word

router = APIRouter()

UPLOAD_DIR = "app/audio_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Modèles Pydantic ──────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    texte: str

class TTSSegmentsRequest(BaseModel):
    segments: list[dict]

class STTSegmentsRequest(BaseModel):
    url_audio:  str
    collect_id: Optional[str] = None

class ValidateSegmentationRequest(BaseModel):
    collect_id: str

class UpdateSegmentRequest(BaseModel):
    segment_id: str
    new_text:   str


# ── STT — Transcription + Traduction ─────────────────────────────────────────

@router.post(
    "/transcriptor/stt",
    summary = "Transcrit un audio en corse et traduit en français",
    tags    = ["Transcription"],
)
async def stt_transcribe(
    request: Request,
    file:    UploadFile = File(...),
) -> JSONResponse:
    """
    Reçoit un fichier audio, le transcrit en corse
    et retourne aussi la traduction en français.
    """

    user_id = request.cookies.get("session_user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Non connecté."})

    # ── Sauvegarde temporaire du fichier ──────────────
    ext       = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    tmp_path  = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")

    with open(tmp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = transcribe_and_translate(tmp_path)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur STT : {e}"},
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return JSONResponse(
        status_code=200,
        content={
            "success":          True,
            "transcription_co": result["transcription_co"],
            "traduction_fr":    result["traduction_fr"],
        },
    )


@router.post(
    "/transcriptor/stt/segments",
    summary = "Transcrit un audio en segments horodatés",
    tags    = ["Transcription"],
)
async def stt_segments(
    request: Request,
    body:    STTSegmentsRequest,
) -> JSONResponse:
    """
    1. Si collect_id fourni et segmentation déjà validée → charge depuis DB
    2. Sinon → transcrit via Groq et sauvegarde en DB
    """

    user_id = request.cookies.get("session_user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Non connecté."})

    # ── Vérifie si déjà transcrit en DB ──────────────
    if body.collect_id:
        existing = load_segments(body.collect_id)
        if existing and existing["validation"]:
            print(f"[STT SEGMENTS] ✅ Chargé depuis DB (déjà validé) collect_id={body.collect_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success":    True,
                    "segments":   existing["segments"],
                    "from_cache": True,
                    "validation": True,
                },
            )

    print(f"[STT SEGMENTS] URL reçue : {body.url_audio}")
    tmp_path = os.path.join(UPLOAD_DIR, f"{user_id}_audio.wav")

    try:
        import httpx
        audio_response = httpx.get(body.url_audio, timeout=60)
        audio_response.raise_for_status()

        with open(tmp_path, "wb") as f:
            f.write(audio_response.content)

        print(f"[STT SEGMENTS] Audio téléchargé : {len(audio_response.content)} bytes")
        segments = transcribe_segments(tmp_path)
        print(f"[STT SEGMENTS] ✅ {len(segments)} segments retournés")

        # ── Sauvegarde en DB ──────────────────────────
        if body.collect_id:
            save_segments(body.collect_id, segments)
            print(f"[STT SEGMENTS] ✅ Segments sauvegardés en DB")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[STT SEGMENTS] ❌ {type(e).__name__} : {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur STT segments : {e}"},
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return JSONResponse(
        status_code=200,
        content={"success": True, "segments": segments, "from_cache": False, "validation": False},
    )


# ── Validation des 3 transcripteurs ──────────────────────────────────────────

@router.post(
    "/transcriptor/validate",
    summary = "Valide la transcription — passe traitement_transcription à 1",
    tags    = ["Transcription"],
)
async def validate_transcription(
    request: Request,
    body:    ValidateSegmentationRequest,
) -> JSONResponse:

    user_id = request.cookies.get("session_user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Non connecté."})

    try:
        validate_segmentation(body.collect_id)
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

    return JSONResponse(status_code=200, content={"success": True, "message": "Transcription validée."})


# ── Mise à jour d'un segment ──────────────────────────────────────────────────

@router.put(
    "/transcriptor/segment",
    summary = "Met à jour le texte d'un segment",
    tags    = ["Transcription"],
)
async def update_segment(
    request: Request,
    body:    UpdateSegmentRequest,
) -> JSONResponse:

    user_id = request.cookies.get("session_user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Non connecté."})

    try:
        update_segment_word(body.segment_id, body.new_text)
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

    return JSONResponse(status_code=200, content={"success": True})


# ── TTS — Synthèse vocale ─────────────────────────────────────────────────────

@router.post(
    "/transcriptor/tts",
    summary = "Synthétise un texte corse en audio",
    tags    = ["Transcription"],
)
async def tts_synthesize(
    request: Request,
    body:    TTSRequest,
) -> JSONResponse:
    """
    Convertit un texte corse en fichier audio WAV.
    Retourne le chemin du fichier généré.
    """

    user_id = request.cookies.get("session_user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Non connecté."})

    try:
        url_audio = synthesize(body.texte)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur TTS : {e}"},
        )

    return JSONResponse(
        status_code=200,
        content={"success": True, "url_audio": url_audio},
    )


@router.post(
    "/transcriptor/tts/segments",
    summary = "Synthétise une liste de segments textuels",
    tags    = ["Transcription"],
)
async def tts_segments(
    request: Request,
    body:    TTSSegmentsRequest,
) -> JSONResponse:

    user_id = request.cookies.get("session_user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "Non connecté."})

    try:
        results = synthesize_segments(body.segments)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur TTS segments : {e}"},
        )

    return JSONResponse(
        status_code=200,
        content={"success": True, "segments": results},
    )


# ── Téléchargement du fichier audio TTS ──────────────────────────────────────

@router.get(
    "/transcriptor/tts/download/{filename}",
    summary = "Télécharge un fichier audio TTS généré",
    tags    = ["Transcription"],
)
async def tts_download(filename: str) -> FileResponse:
    path = os.path.join("app/tts_output", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé.")
    return FileResponse(path, media_type="audio/wav", filename=filename)
