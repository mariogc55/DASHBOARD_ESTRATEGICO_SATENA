"""Utilidades transversales: branding, cifrado y formateo."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

SATENA_AZUL = "#0B3D91"
SATENA_AZUL_OSCURO = "#072A66"
SATENA_BLANCO = "#FFFFFF"
SATENA_VERDE = "#198754"
SATENA_ROJO = "#DC3545"
SATENA_AMARILLO = "#FFC107"

PSI_UMBRAL_CRITICO = 0.25
FAIRNESS_DP_MIN = 0.80
FAIRNESS_DP_MAX = 1.25
FAIRNESS_TPR_MAX_DIFF = 0.05
FAIRNESS_PPV_MAX_DIFF = 0.05

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SECRETS_DIR = PROJECT_ROOT / ".secrets"
FERNET_KEY_FILE = SECRETS_DIR / "fernet.key"

DEFAULT_USER = "admin.satena"
DEFAULT_PASSWORD = "Satena@2026!"


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or "satena-ia-governance"
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return base64.urlsafe_b64encode(digest).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def get_or_create_fernet() -> Fernet:
    ensure_directories()
    if not FERNET_KEY_FILE.exists():
        FERNET_KEY_FILE.write_bytes(Fernet.generate_key())
    key = FERNET_KEY_FILE.read_bytes()
    return Fernet(key)


def encrypt_text(plain: str) -> str:
    fernet = get_or_create_fernet()
    token = fernet.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: str) -> str | None:
    fernet = get_or_create_fernet()
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


def format_percent(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def semaforo_class(en_cumplimiento: bool) -> str:
    return "semaforo-verde" if en_cumplimiento else "semaforo-rojo"
