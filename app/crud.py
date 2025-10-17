from sqlmodel import Session, select
from .database import engine
from .models import User
from passlib.context import CryptContext
from typing import Optional 
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto") 
from datetime import datetime
from sqlmodel import select
from .models import UserSession as SessionModel
def get_session():
    return Session(engine)

# ✅ Создание сессии
def create_session_db(user_id: int, token: str, expires: datetime) -> SessionModel:
    with get_session() as s:
        session = SessionModel(token=token, user_id=user_id, created=datetime.utcnow(), expires=expires)
        s.add(session)
        s.commit()
        s.refresh(session)
        return session

# ✅ Получение сессии по токену
def get_session_by_token(token: str) -> Optional[SessionModel]:
    with get_session() as s:
        statement = select(SessionModel).where(SessionModel.token == token)
        result = s.exec(statement).first()
        if result and result.expires > datetime.utcnow():
            return result
        return None

# ✅ Удаление сессии
def delete_session_db(token: str) -> bool:
    with get_session() as s:
        statement = select(SessionModel).where(SessionModel.token == token)
        result = s.exec(statement).first()
        if not result:
            return False
        s.delete(result)
        s.commit()
        return True

# Пользователи
def get_user_by_id(user_id: int) -> Optional[User]:
    with get_session() as s:
        return s.get(User, user_id)

def get_user_by_email(email: str) -> Optional[User]:
    with get_session() as s:
        statement = select(User).where(User.email == email)
        return s.exec(statement).first()
    
def get_user_by_login(login: str) -> Optional[User]:
    with get_session() as s:
        statement = select(User).where(User.nickname == login)
        return s.exec(statement).first()

def list_users() -> list[User]:
    with get_session() as s:
        statement = select(User).order_by(User.id)
        return s.exec(statement).all()

def create_user(nickname: str, email: str, password_plain: str, **kwargs) -> User:
    with get_session() as s:
        password_hash = pwd_context.hash(password_plain)
        user = User(nickname=nickname, email=email, password_hash=password_hash, **kwargs)
        s.add(user)
        s.commit()
        s.refresh(user)
        return user

def create_user_raw(id: int, nickname: str, email: str, password_plain: str, **kwargs) -> User:
    with get_session() as s:
        existing = s.get(User, id)
        if existing:
            return existing
        password_hash = pwd_context.hash(password_plain)
        user = User(id=id, nickname=nickname, email=email, password_hash=password_hash, **kwargs)
        s.add(user)
        s.commit()
        s.refresh(user)
        return user

def update_user(user_id: int, **fields) -> Optional[User]:
    with get_session() as s:
        user = s.get(User, user_id)
        if not user:
            return None
        for key, value in fields.items():
            # Разрешаем ЯВНО ставить None в avatar
            if key == "avatar":
                setattr(user, "avatar", value)  # даже если None — ок, будет NULL
            else:
                if value is not None:
                    setattr(user, key, value)
                # Если value is None для других полей — пропускаем (как раньше)
        s.add(user)
        s.commit()
        s.refresh(user)
        return user

def delete_user(user_id: int) -> bool:
    with get_session() as s:
        user = s.get(User, user_id)
        if not user:
            return False
        s.delete(user)
        s.commit()
        return True

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)