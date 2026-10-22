
import time
import secrets
import hmac

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database import admins_collection
from security import verify_password


router = APIRouter()
templates = Jinja2Templates(directory="templates")

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 10 * 60
LOGIN_BLOCK_SECONDS = 15 * 60

login_attempts = {}
login_blocked_until = {}


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token

    return token


def validate_csrf_token(
    request: Request,
    csrf_token: str,
) -> None:
    session_token = request.session.get("csrf_token")

    if (
        not session_token
        or not csrf_token
        or not hmac.compare_digest(session_token, csrf_token)
    ):
        raise HTTPException(
            status_code=403,
            detail="درخواست نامعتبر است.",
        )


class AdminLoginRequired(Exception):
    """خطای اختصاصی برای صفحات نیازمند ورود مدیر."""
    pass


def require_admin(request: Request):
    admin_id = request.session.get("admin_id")

    if not admin_id:
        raise AdminLoginRequired()

    try:
        mongo_admin_id = ObjectId(admin_id)
    except (InvalidId, TypeError):
        request.session.clear()
        raise AdminLoginRequired()

    admin = admins_collection.find_one({"_id": mongo_admin_id})

    if admin is None:
        request.session.clear()
        raise AdminLoginRequired()

    return admin


@router.get("/login", response_class=HTMLResponse)
def show_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None},
    )


@router.post("/login")
def login_admin(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    now = time.monotonic()

    blocked_until = login_blocked_until.get(client_ip, 0)

    if now < blocked_until:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": (
                    "تلاش‌های ورود بیش از حد مجاز بوده است. "
                    "لطفاً ۱۵ دقیقه دیگر دوباره تلاش کنید."
                )
            },
            status_code=429,
        )

    if blocked_until:
        login_blocked_until.pop(client_ip, None)
        login_attempts.pop(client_ip, None)

    attempts = login_attempts.get(client_ip, [])

    attempts = [
        attempt_time
        for attempt_time in attempts
        if now - attempt_time < LOGIN_WINDOW_SECONDS
    ]

    login_attempts[client_ip] = attempts

    admin = admins_collection.find_one({
        "username": username.strip()
    })

    if (
        admin is None
        or not verify_password(
            password,
            admin["hashed_password"],
        )
    ):
        attempts.append(now)
        login_attempts[client_ip] = attempts

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            login_blocked_until[client_ip] = (
                now + LOGIN_BLOCK_SECONDS
            )

            login_attempts.pop(client_ip, None)

            error_message = (
                "تعداد تلاش‌های ناموفق بیش از حد مجاز است. "
                "ورود شما برای ۱۵ دقیقه مسدود شد."
            )
        else:
            error_message = "نام کاربری یا رمز عبور اشتباه است."

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": error_message},
            status_code=401,
        )

    login_attempts.pop(client_ip, None)
    login_blocked_until.pop(client_ip, None)

    request.session.clear()
    request.session["admin_id"] = str(admin["_id"])

    return RedirectResponse(
        url="/",
        status_code=303,
    )


@router.post("/logout")
async def logout(
    request: Request,
    csrf_token: str = Form(...),
    admin: dict = Depends(require_admin),
):
    validate_csrf_token(request, csrf_token)

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303,
    )
