# ================================================
# tts_mms.py
# Text-to-Speech via Hugging Face Inference API
# Modèle : facebook/mms-tts-cos (corse)
# ================================================

import os
import uuid
import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN       = os.getenv("HF_TOKEN", "")
HF_API_URL_TTS = "https://api-inference.huggingface.co/models/facebook/mms-tts-cos"
OUTPUT_DIR     = "app/tts_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

if not HF_TOKEN:
    print("[TTS] ⚠️  HF_TOKEN non défini — les appels TTS échoueront.")

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type":  "application/json",
}


def synthesize(texte: str, filename: str | None = None) -> str:
    """
    Envoie un texte corse à l'API Hugging Face TTS.
    Retourne le chemin du fichier WAV généré.
    """

    if not texte.strip():
        raise ValueError("Le texte ne peut pas être vide.")

    response = httpx.post(
        HF_API_URL_TTS,
        headers = HEADERS,
        json    = {"inputs": texte},
        timeout = 60,
    )
    response.raise_for_status()

    fname       = filename or f"tts_{uuid.uuid4().hex[:8]}.wav"
    output_path = os.path.join(OUTPUT_DIR, fname)

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"[TTS] ✅ Audio généré : {output_path}")
    return output_path


def synthesize_segments(segments: list[dict]) -> list[dict]:
    """
    Synthétise une liste de segments textuels.
    Entrée  : [{ "id": 1, "texte": "..." }, ...]
    Sortie  : [{ "id": 1, "texte": "...", "url_audio": "..." }, ...]
    """
    results = []
    for seg in segments:
        texte = seg.get("texte", "").strip()
        if not texte:
            results.append({**seg, "url_audio": None})
            continue
        try:
            fname     = f"tts_seg_{seg['id']}_{uuid.uuid4().hex[:6]}.wav"
            url_audio = synthesize(texte, filename=fname)
            results.append({**seg, "url_audio": url_audio})
        except Exception as e:
            print(f"[TTS] ❌ Erreur segment {seg.get('id')} : {e}")
            results.append({**seg, "url_audio": None})

    return results
