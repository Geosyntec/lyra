import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from lyra.core.config import settings

security = HTTPBasic(auto_error=False)


def is_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials is None:
        return False

    correct_username = secrets.compare_digest(
        credentials.username, settings.ADMIN_USERNAME
    )
    correct_password = secrets.compare_digest(credentials.password, settings.SECRET_KEY)

    return correct_username and correct_password


def authenticate_admin_access(is_administrator: bool = Depends(is_admin)):

    if is_administrator:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Basic"},
    )
