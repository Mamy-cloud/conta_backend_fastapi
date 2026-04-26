# ================================================
# stt_whisper.py
# Speech-to-Text via Hugging Face Inference API
# Modèle : openai/whisper-large-v3
# ================================================

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN       = os.getenv("HF_TOKEN", "")
HF_API_URL_STT = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"

if not HF_TOKEN:
    print("[STT] ⚠️  HF_TOKEN non défini — les appels STT échoueront.")

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
}


def transcribe_and_translate(audio_path: str) -> dict:
    """
    Transcrit un fichier audio et traduit en français.
    """
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    # ── Transcription ────────────────────────────────
    response_co = httpx.post(
        HF_API_URL_STT,
        headers = HEADERS,
        content = audio_bytes,
        timeout = 120,
    )
    response_co.raise_for_status()
    transcription_co = response_co.json().get("text", "").strip()

    # ── Traduction ────────────────────────────────────
    response_fr = httpx.post(
        HF_API_URL_STT,
        headers = {**HEADERS, "Content-Type": "audio/mpeg"},
        content = audio_bytes,
        timeout = 120,
        params  = {"task": "translate"},
    )
    response_fr.raise_for_status()
    traduction_fr = response_fr.json().get("text", "").strip()

    return {
        "transcription_co": transcription_co,
        "traduction_fr":    traduction_fr,
    }


def transcribe_segments(audio_path: str) -> list[dict]:
    """
    Transcrit l'audio avec timestamps par segment.
    """
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    response = httpx.post(
        HF_API_URL_STT,
        headers = HEADERS,
        content = audio_bytes,
        timeout = 120,
    )
    response.raise_for_status()
    data = response.json()

    print(f"[STT] Réponse HF : {data}")

    segments = []

    # ── Si la réponse contient des chunks horodatés ───
    for chunk in data.get("chunks", []):
        ts    = chunk.get("timestamp", [0, 0])
        debut = _format_time(ts[0] or 0)
        fin   = _format_time(ts[1] or 0)
        segments.append({
            "debut": debut,
            "fin":   fin,
            "texte": chunk.get("text", "").strip(),
        })

    # ── Sinon retourne tout comme un seul segment ─────
    if not segments and data.get("text"):
        segments.append({
            "debut": "00:00",
            "fin":   "00:00",
            "texte": data["text"].strip(),
        })

    return segments


def _format_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"
