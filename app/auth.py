from fastapi import Request, Form
from starlette.responses import RedirectResponse
from .crud import get_user_by_email, verify_password
from .crud import create_user
from .crud import get_user_by_id
from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import HTTPException, status

# Для простоты используем сессии через cookie без внешних библиотек
from fastapi import Cookie
from datetime import datetime, timedelta
import os
import base64

SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')

# Простая реализация сессионной cookie (НЕ ПРОДАКШН, для шаблона)
SESSIONS: dict[str, dict] = {}

def create_session(user_id: int) -> str:
    token = base64.urlsafe_b64encode(os.urandom(24)).decode()
    SESSIONS[token] = {"user_id": user_id, "created": datetime.now()}
    return token

def get_current_user(session_token: Optional[str] = Cookie(None)):
    if not session_token:
        return None
    data = SESSIONS.get(session_token)
    if not data:
        return None
    return get_user_by_id(data['user_id'])

def destroy_session(session_token: Optional[str] = Cookie(None)):
    if session_token and session_token in SESSIONS:
        del SESSIONS[session_token]