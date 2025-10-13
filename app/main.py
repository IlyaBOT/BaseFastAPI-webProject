# app/main.py
from fastapi import FastAPI, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel
from .database import engine
from .crud import (
    create_user,
    get_user_by_email,
    get_user_by_login,
    verify_password,
    list_users,
    get_user_by_id,
    update_user,
    delete_user,
    pwd_context,
)
from .auth import create_session, get_current_user, destroy_session
from typing import Optional
import pyotp
import qrcode
import io
import base64
from datetime import timedelta

app = FastAPI()
app.mount('/static', StaticFiles(directory='app/static'), name='static')
templates = Jinja2Templates(directory='app/templates')

# создаём таблицы при старте
@app.on_event('startup')
def on_startup():
    SQLModel.metadata.create_all(engine)

# Главная
@app.get('/', response_class=HTMLResponse)
def index(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse('index.html', {'request': request, 'user': current_user})

# Регистрация (GET/POST)
@app.get('/register', response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse('register.html', {'request': request, 'error': None})

@app.post('/register')
def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    # Валидация паролей
    if password != confirm_password:
        return templates.TemplateResponse('register.html', {'request': request, 'error': 'Пароли не совпадают'})

    # Проверка существования email
    if get_user_by_email(email):
        return templates.TemplateResponse('register.html', {'request': request, 'error': 'Email уже зарегистрирован'})

    # Создаём пользователя. Передаём пустые optional-поля явно.
    # Внутри create_user ожидаем nickname/email/password_plain — поэтому мапим username -> nickname.
    user = create_user(
        nickname=username,
        email=email,
        password_plain=password,
        birthday=None,
        bio="",
        phone=""
    )

    # Логиним пользователя: создаём сессию и ставим cookie
    resp = RedirectResponse(url=f'/user/{user.id}', status_code=303)
    token = create_session(user.id)
    resp.set_cookie('session_token', token, httponly=True)
    return resp

# Логин (оставляем как было)
@app.get('/login', response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'error': None})

@app.post('/login')
def login_post(request: Request, login: str = Form(...), password: str = Form(...)):
    user = get_user_by_login(login)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse('login.html', {'request': request, 'error': 'Неправильные учётные данные'})
    # Если включена 2FA — перенаправляем на страницу ввода кода
    if user.is_2fa_enabled:
        resp = RedirectResponse(url=f'/2fa_check?user_id={user.id}', status_code=303)
        resp.set_cookie('tmp_user', str(user.id), httponly=True)
        return resp
    resp = RedirectResponse(url=f'/user/{user.id}', status_code=303)
    token = create_session(user.id)
    # кука на 30 дней, HttpOnly для безопасности
    resp.set_cookie(
        key="session_token",
        value=token,
        max_age=60*60*24*30,       # 30 дней в секундах
        httponly=True,
        samesite="lax"
    )
    return resp

# 2FA проверка (GET показывает форму, POST проверяет код)
@app.get('/2fa_check', response_class=HTMLResponse)
def twofa_get(request: Request, user_id: Optional[int] = None):
    # Универсальная страница: если user_id указан — это этап настройки (редиректят на /user/.../2fa),
    # если нет — это проверка при логине (checking=True)
    return templates.TemplateResponse('2fa_setup.html', {'request': request, 'checking': True, 'error': None})

@app.post('/2fa_check')
def twofa_post(request: Request, code: str = Form(...)):
    tmp = request.cookies.get('tmp_user')
    if not tmp:
        return RedirectResponse('/login')
    user_id = int(tmp)
    user = get_user_by_id(user_id)
    if not user or not user.otp_secret:
        return templates.TemplateResponse('2fa_setup.html', {'request': request, 'checking': True, 'error': '2FA не настроена'})
    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(code):
        return templates.TemplateResponse('2fa_setup.html', {'request': request, 'checking': True, 'error': 'Неверный код'})
    # всё ок — создаём сессию
    resp = RedirectResponse(url=f'/user/{user.id}', status_code=303)
    token = create_session(user.id)
    resp.set_cookie('session_token', token, httponly=True)
    resp.delete_cookie('tmp_user')
    return resp

# Профиль
@app.get('/user/{user_id}', response_class=HTMLResponse)
def profile(request: Request, user_id: int, current_user=Depends(get_current_user)):
    target = get_user_by_id(user_id)
    if not target:
        return Response('Пользователь не найден', status_code=404)
    editable = current_user and (current_user.id == target.id or current_user.id == 1)
    return templates.TemplateResponse('profile.html', {'request': request, 'user': current_user, 'target': target, 'editable': editable})

@app.get('/user/{user_id}/edit', response_class=HTMLResponse)
def edit_profile_get(request: Request, user_id: int, current_user=Depends(get_current_user)):
    if not current_user or not (current_user.id == user_id or current_user.id == 1):
        return RedirectResponse('/login')
    target = get_user_by_id(user_id)
    return templates.TemplateResponse('edit_profile.html', {'request': request, 'target': target, 'error': None})

@app.post('/user/{user_id}/edit')
def edit_profile_post(
    request: Request,
    user_id: int,
    nickname: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    password_confirm: Optional[str] = Form(None),
    birthday: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
):
    if not current_user or not (current_user.id == user_id or current_user.id == 1):
        return RedirectResponse('/login')
    if password and password != password_confirm:
        target = get_user_by_id(user_id)
        return templates.TemplateResponse('edit_profile.html', {'request': request, 'target': target, 'error': 'Пароли не совпадают'})
    fields = {}
    if nickname is not None:
        fields['nickname'] = nickname
    if email is not None:
        fields['email'] = email
    if birthday:
        fields['birthday'] = birthday
    if bio is not None:
        fields['bio'] = bio
    if phone is not None:
        fields['phone'] = phone
    if password:
        # хешируем пароль и передаём как password_hash (update_user просто ставит поле)
        fields['password_hash'] = pwd_context.hash(password)
    update_user(user_id, **fields)
    return RedirectResponse(f'/user/{user_id}', status_code=303)

# 2FA setup (enable/disable)
@app.get('/user/{user_id}/2fa', response_class=HTMLResponse)
def setup_2fa_get(request: Request, user_id: int, current_user=Depends(get_current_user)):
    if not current_user or not (current_user.id == user_id or current_user.id == 1):
        return RedirectResponse('/login')
    user = get_user_by_id(user_id)
    if not user:
        return Response('Пользователь не найден', status_code=404)
    # если нет секрета — генерируем и сохраняем
    if not user.otp_secret:
        secret = pyotp.random_base32()
        update_user(user_id, otp_secret=secret)
        user = get_user_by_id(user_id)
    otpauth = pyotp.totp.TOTP(user.otp_secret).provisioning_uri(name=user.email, issuer_name='FastAPIApp')
    img = qrcode.make(otpauth)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    return templates.TemplateResponse('2fa_setup.html', {'request': request, 'user': current_user, 'qr': img_b64, 'secret': user.otp_secret, 'checking': False})

@app.post('/user/{user_id}/2fa_disable')
def disable_2fa(user_id: int, current_user=Depends(get_current_user)):
    if not current_user or not (current_user.id == user_id or current_user.id == 1):
        return RedirectResponse('/login')
    update_user(user_id, is_2fa_enabled=False, otp_secret=None)
    return RedirectResponse(f'/user/{user_id}')

@app.post('/user/{user_id}/2fa_enable')
def enable_2fa(user_id: int, code: str = Form(...), current_user=Depends(get_current_user)):
    if not current_user or not (current_user.id == user_id or current_user.id == 1):
        return RedirectResponse('/login')
    user = get_user_by_id(user_id)
    if not user or not user.otp_secret:
        return RedirectResponse(f'/user/{user_id}/2fa')
    totp = pyotp.TOTP(user.otp_secret)
    if totp.verify(code):
        update_user(user_id, is_2fa_enabled=True)
    return RedirectResponse(f'/user/{user_id}')

# Админ: список пользователей, создание, удаление
@app.get('/admin', response_class=HTMLResponse)
def admin_panel(request: Request, current_user=Depends(get_current_user)):
    if not current_user or current_user.id != 1:
        return RedirectResponse('/login')
    users = list_users()
    return templates.TemplateResponse('admin.html', {'request': request, 'users': users})


@app.post('/admin/create')
def admin_create(
    nickname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    current_user=Depends(get_current_user),
):
    if not current_user or current_user.id != 1:
        return RedirectResponse('/login')
    create_user(nickname=nickname, email=email, password_plain=password)
    return RedirectResponse('/admin')

@app.post('/admin/delete')
def admin_delete(user_id: int = Form(...), current_user=Depends(get_current_user)):
    if not current_user or current_user.id != 1:
        return RedirectResponse('/login')
    if user_id == 1:
        return RedirectResponse('/admin')
    delete_user(user_id)
    return RedirectResponse('/admin')

# Logout
@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        destroy_session(token)
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_token")
    return response
