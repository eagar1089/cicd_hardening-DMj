"""Firebase auth dependency for protecting routes."""
import json
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Ensure FIREBASE_* env vars are available regardless of working directory
BACKEND_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=BACKEND_ENV_PATH)
load_dotenv()


def _build_firebase_cert_from_env() -> dict | None:
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            cert_data = json.loads(service_account_json)
            if all(k in cert_data for k in ("project_id", "private_key", "client_email")):
                cert_data["private_key"] = cert_data["private_key"].replace("\\n", "\n")
                return cert_data
            logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON is missing required keys")
        except json.JSONDecodeError:
            logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON")

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

    if not project_id or not private_key or not client_email:
        return None

    # Backward-compatible support for split FIREBASE_* vars.
    cert_data = {
        "project_id": project_id,
        "private_key": private_key.replace("\\n", "\n"),
        "client_email": client_email,
    }
    cert_data.update({
        "type": os.getenv("FIREBASE_ACCOUNT_TYPE", "service_account"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
    })
    return cert_data


def _initialize_firebase_admin() -> None:
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    cert_data = _build_firebase_cert_from_env()
    if cert_data:
        try:
            cred = credentials.Certificate(cert_data)
            firebase_admin.initialize_app(
                cred,
                {
                    "projectId": cert_data["project_id"],
                },
            )
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", cert_data["project_id"])
            logger.info("Firebase Admin initialized from FIREBASE_* env vars (projectId=%s)", cert_data["project_id"])
            return
        except Exception as exc:
            logger.exception("Failed to initialize Firebase from FIREBASE_* env vars: %s", exc)
            logger.warning("Falling back to default application credentials")

    firebase_admin.initialize_app()
    logger.info("Firebase Admin initialized using default application credentials")


_initialize_firebase_admin()


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to verify Firebase ID token from Authorization header.
    Returns the decoded token (user info).
    """
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.exception("Firebase token verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
        )


async def verify_firebase_token_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[dict]:
    """
    Optional auth dependency for read-only endpoints.
    Returns decoded token when valid, otherwise returns None.
    """
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.warning("Optional Firebase token verification failed: %s", str(e))
        return None

