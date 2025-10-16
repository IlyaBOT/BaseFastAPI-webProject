from fastapi import Cookie
from typing import Optional
from datetime import datetime, timedelta
import os, base64

from .crud import (
    get_user_by_id,
    create_session_db,
    get_session_by_token,
    delete_session_db,
)

SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')


# Создание сессии и запись в БД
def create_session(user_id: int) -> str:
    token = base64.urlsafe_b64encode(os.urandom(24)).decode()
    expires = datetime.utcnow() + timedelta(days=7)  # сессия живёт 7 дней
    create_session_db(user_id=user_id, token=token, expires=expires)
    return token


# Получение текущего пользователя по cookie
def get_current_user(session_token: Optional[str] = Cookie(None)):
    if not session_token:
        return None
    session = get_session_by_token(session_token)
    if not session:
        return None
    return get_user_by_id(session.user_id)


# Удаление сессии (разлогин)
def destroy_session(session_token: Optional[str] = Cookie(None)):
    if session_token:
        delete_session_db(session_token)