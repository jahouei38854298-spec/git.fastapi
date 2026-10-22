
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from auth import (
    AdminLoginRequired,
    router as auth_router,
)
from students import router as students_router


# بارگذاری متغیرهای محیطی
load_dotenv()


# ==========================================
# 1. تنظیمات اصلی برنامه
# ==========================================

app = FastAPI()


# کلید محرمانه نشست مدیر
SECRET_KEY = os.environ.get("SESSION_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "متغیر SESSION_SECRET_KEY تنظیم نشده است."
    )


# تنظیمات نشست
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="user_session",
    max_age=60 * 60,
    same_site="lax",
    https_only=False,
)


# فایل‌های استاتیک
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


# ==========================================
# 2. مدیریت خطای احراز هویت
# ==========================================

@app.exception_handler(AdminLoginRequired)
async def admin_login_required_handler(
    request: Request,
    exc: AdminLoginRequired,
):
    return RedirectResponse(
        url="/login",
        status_code=303,
    )


# ==========================================
# 3. اتصال روترها
# ==========================================

app.include_router(auth_router)
app.include_router(students_router)
