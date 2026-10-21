
from pwdlib import PasswordHash

# آماده‌سازی ابزار هش رمز عبور
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """تبدیل رمز عبور به هش"""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """بررسی صحت رمز عبور"""
    return password_hash.verify(
        plain_password,
        hashed_password
    )
