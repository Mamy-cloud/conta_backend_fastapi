# ================================================
# stt_whisper.py
# Speech-to-Text via Groq API
# Modèle : whisper-large-v3
# ================================================

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL   = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_API_URL_T = "https://api.groq.com/openai/v1/audio/translations"

if not GROQ_API_KEY:
    print("[STT] ⚠️  GROQ_API_KEY non défini — les appels STT échoueront.")

HEADERS = {"Authorization": f"Bearer {GROQ_API_KEY}"}


def transcribe_and_translate(audio_path: str) -> dict:
    """
    Transcrit un fichier audio et traduit en français.
    Retourne { "transcription_co": str, "traduction_fr": str }
    """

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    filename = os.path.basename(audio_path)

    # ── Transcription (langue source) ────────────────
    response_co = httpx.post(
        GROQ_API_URL,
        headers = HEADERS,
        files   = {"file": (filename, audio_bytes, "audio/mpeg")},
        data    = {
            "model":           "whisper-large-v3",
            "response_format": "json",
        },
        timeout = 120,
    )
    response_co.raise_for_status()
    transcription_co = response_co.json().get("text", "").strip()

    # ── Traduction vers l'anglais puis français ───────
    response_fr = httpx.post(
        GROQ_API_URL_T,
        headers = HEADERS,
        files   = {"file": (filename, audio_bytes, "audio/mpeg")},
        data    = {
            "model":           "whisper-large-v3",
            "response_format": "json",
        },
        timeout = 120,
    )
    response_fr.raise_for_status()
    traduction_fr = response_fr.json().get("text", "").strip()

    return {
        "transcription_co": transcription_co,
        "traduction_fr":    traduction_fr,
    }


def _convert_to_mp3(input_path: str) -> str:
    """Convertit n'importe quel audio en mp3 via ffmpeg."""
    import subprocess
    output_path = input_path.rsplit(".", 1)[0] + "_converted.mp3"
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-ar", "16000",   # 16kHz suffisant pour Whisper
        "-ac", "1",       # mono
        "-b:a", "64k",    # qualité suffisante, fichier léger
        output_path, "-y", "-loglevel", "error"
    ], check=True)
    print(f"[STT] Converti en mp3 : {output_path}")
    return output_path


def transcribe_segments(audio_path: str) -> list[dict]:
    """
    Transcrit l'audio avec timestamps par segment.
    Retourne [{ "debut": "00:00", "fin": "00:05", "texte": "..." }, ...]
    """

    # ── Conversion en mp3 ─────────────────────────────
    mp3_path = _convert_to_mp3(audio_path)

    try:
        with open(mp3_path, "rb") as f:
            audio_bytes = f.read()

        filename = os.path.basename(mp3_path)
        print(f"[STT] Fichier mp3 : {filename}, Taille : {len(audio_bytes)} bytes")

        response = httpx.post(
            GROQ_API_URL,
            headers = HEADERS,
            files   = {"file": (filename, audio_bytes, "audio/mpeg")},
            data    = {
                "model":                     "whisper-large-v3",
                "response_format":           "verbose_json",
                "timestamp_granularities[]": "segment",
            },
            timeout = 120,
        )

        if not response.is_success:
            print(f"[STT] ❌ Groq error response : {response.text}")

        response.raise_for_status()
        data = response.json()

        print(f"[STT] Réponse Groq keys : {list(data.keys())}")

        segments = []
        for seg in data.get("segments", []):
            debut = _format_time(seg.get("start", 0))
            fin   = _format_time(seg.get("end",   0))
            segments.append({
                "debut": debut,
                "fin":   fin,
                "texte": seg.get("text", "").strip(),
            })

        if not segments and data.get("text"):
            segments.append({
                "debut": "00:00",
                "fin":   "00:00",
                "texte": data["text"].strip(),
            })

        return segments

    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)


def _format_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"
