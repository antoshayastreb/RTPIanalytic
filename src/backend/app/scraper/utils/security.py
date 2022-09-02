from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, status, HTTPException
import secrets

from scraper.config import settings

#HTTP Basic Auth
security = HTTPBasic()

correct_username_bytes = settings.AUTH_USERNAME.encode("utf8")
correct_password_bytes = settings.AUTH_PASSWORD.encode("utf8")

def check_http_basic(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    current_password_bytes = credentials.password.encode("utf8")

    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )

    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )