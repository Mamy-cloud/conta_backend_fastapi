""" import os
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

BUCKET_NAME = "collect_audio"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def upload_audio(file_bytes: bytes, file_name: str) -> str:
   
    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "audio/mpeg"}
    )
    return get_public_url(file_name)


def delete_audio(file_name: str) -> None:
    
    supabase.storage.from_(BUCKET_NAME).remove([file_name])


def list_audios() -> list:
   
    return supabase.storage.from_(BUCKET_NAME).list()


def download_audio(file_name: str) -> bytes:
    
    return supabase.storage.from_(BUCKET_NAME).download(file_name)


def get_public_url(file_name: str) -> str:
    
    return supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)



def upload_image(file_bytes: bytes, file_name: str) -> str:
    
    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "image/jpeg"}
    )
    return get_public_url(file_name)
 """
import os
from supabase import create_client, Client

BUCKET_NAME = "collect_audio"

# -----------------------------
# SAFE SUPABASE INITIALIZATION
# -----------------------------

_supabase: Client | None = None


def get_supabase() -> Client:
    """Initialise Supabase uniquement quand nécessaire (évite crash au import)."""
    global _supabase

    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise RuntimeError("Supabase env variables missing")

        _supabase = create_client(url, key)

    return _supabase


# -----------------------------
# STORAGE FUNCTIONS
# -----------------------------

def upload_audio(file_bytes: bytes, file_name: str) -> str:
    """Upload un fichier audio et retourne l'URL publique."""
    supabase = get_supabase()

    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "audio/mpeg"}
    )

    return get_public_url(file_name)


def delete_audio(file_name: str) -> None:
    """Supprime un fichier audio."""
    supabase = get_supabase()

    supabase.storage.from_(BUCKET_NAME).remove([file_name])


def list_audios() -> list:
    """Liste les fichiers audio."""
    supabase = get_supabase()

    return supabase.storage.from_(BUCKET_NAME).list()


def download_audio(file_name: str) -> bytes:
    """Télécharge un fichier audio."""
    supabase = get_supabase()

    return supabase.storage.from_(BUCKET_NAME).download(file_name)


def get_public_url(file_name: str) -> str:
    """Retourne l'URL publique d'un fichier."""
    supabase = get_supabase()

    return supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)


# -----------------------------
# IMAGE UPLOAD
# -----------------------------

def upload_image(file_bytes: bytes, file_name: str) -> str:
    """Upload une image et retourne l'URL publique."""
    supabase = get_supabase()

    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "image/jpeg"}
    )

    return get_public_url(file_name)